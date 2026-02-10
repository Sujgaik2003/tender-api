"""
Response API Routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime

from app.core.supabase import get_supabase_client
from app.core.security import get_current_user
from app.schemas import (
    ResponseResponse,
    ResponseUpdate,
    GenerateResponsesRequest,
)
from app.services.composer import get_composer
from app.services.matcher import get_matcher

router = APIRouter(prefix="/api", tags=["responses"])


@router.get("/documents/{document_id}/responses", response_model=List[ResponseResponse])
async def get_responses(
    document_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Get responses for document."""
    # Verify document ownership
    # Verify document ownership
    query = supabase.table('documents').select('id').eq('id', document_id)
    if user.get('tenant_id'):
        query = query.eq('tenant_id', user['tenant_id'])
    else:
        query = query.eq('user_id', user['id'])
    doc_result = query.single().execute()
    
    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = supabase.table('responses')\
        .select('*')\
        .eq('document_id', document_id)\
        .order('created_at')\
        .execute()
    
    return result.data


@router.post("/documents/{document_id}/responses/generate")
async def generate_responses(
    document_id: str,
    request: GenerateResponsesRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Generate draft responses for requirements (async - returns immediately)."""
    
    # Verify document ownership
    # Verify document ownership
    query = supabase.table('documents').select('id').eq('id', document_id)
    if user.get('tenant_id'):
        query = query.eq('tenant_id', user['tenant_id'])
    else:
        query = query.eq('user_id', user['id'])
    doc_result = query.single().execute()
    
    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Validate requirement_ids is not empty
    if not request.requirement_ids or len(request.requirement_ids) == 0:
        raise HTTPException(status_code=400, detail="requirement_ids cannot be empty")
    
    # Log count (not all IDs to avoid huge logs)
    print(f"[DEBUG] Requirement IDs count: {len(request.requirement_ids)}")
    
    # Batch size to avoid URL length limits (50 UUIDs per batch is safe)
    BATCH_SIZE = 50
    all_requirements = []
    
    try:
        # Process IDs in batches
        for i in range(0, len(request.requirement_ids), BATCH_SIZE):
            batch_ids = request.requirement_ids[i:i + BATCH_SIZE]
            print(f"[DEBUG] Processing batch {i // BATCH_SIZE + 1}: {len(batch_ids)} IDs")
            
            # Fetch requirements for this batch
            batch_result = supabase.table('requirements')\
                .select('*')\
                .eq('document_id', document_id)\
                .in_('id', batch_ids)\
                .execute()
            
            if batch_result.data:
                all_requirements.extend(batch_result.data)
        
        print(f"[DEBUG] Total requirements found: {len(all_requirements)}")
        
        # Fetch match_results for all requirements (also in batches)
        if all_requirements:
            req_ids = [req['id'] for req in all_requirements]
            all_matches = []
            
            for i in range(0, len(req_ids), BATCH_SIZE):
                batch_req_ids = req_ids[i:i + BATCH_SIZE]
                match_result = supabase.table('match_results')\
                    .select('*')\
                    .in_('requirement_id', batch_req_ids)\
                    .execute()
                if match_result.data:
                    all_matches.extend(match_result.data)
            
            # Map matches to requirements
            matches_by_req = {}
            for m in all_matches:
                req_id = m['requirement_id']
                if req_id not in matches_by_req:
                    matches_by_req[req_id] = []
                matches_by_req[req_id].append(m)
            
            for req in all_requirements:
                req['match_results'] = matches_by_req.get(req['id'], [])
                
    except Exception as e:
        print(f"[ERROR] Failed to query requirements: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to fetch requirements: {str(e)}")
    
    if not all_requirements:
        raise HTTPException(status_code=404, detail="Requirements not found")
    
    # Add to background tasks - process async
    background_tasks.add_task(
        process_response_generation,
        document_id=document_id,
        requirements=all_requirements,
        user_id=user['id'],
        tenant_id=user.get('tenant_id'),
        response_style=request.response_style,
        mode=request.mode,
        tone=request.tone
    )
    
    return {
        "status": "processing",
        "message": "Response generation started. Responses will appear shortly.",
        "requirement_count": len(all_requirements)
    }


async def process_response_generation(
    document_id: str,
    requirements: list,
    user_id: str,
    tenant_id: str = None,
    response_style: str = "professional",
    mode: str = "balanced",
    tone: str = "professional"
):
    """Background task to generate responses."""
    from app.core.supabase import get_supabase
    
    supabase = get_supabase()
    composer = get_composer()
    
    # Fetch company profile context if tenant exists
    company_profile = None
    past_performance = []
    team_profiles = []
    
    if tenant_id:
        try:
            profile_result = supabase.table('company_profiles').select('*').eq('tenant_id', tenant_id).single().execute()
            if profile_result.data:
                company_profile = profile_result.data
            
            # Fetch top 5 past performance items
            pp_result = supabase.table('past_performance').select('*').eq('tenant_id', tenant_id).limit(5).execute()
            past_performance = pp_result.data or []
            
            # Fetch top 5 team profiles
            team_result = supabase.table('team_profiles').select('*').eq('tenant_id', tenant_id).limit(5).execute()
            team_profiles = team_result.data or []
            
        except Exception as e:
            print(f"[WARN] Context fetch failed: {e}")
            pass # Continue with minimal context
            
    for req in requirements:
        try:
            matches = req.get('match_results', [])
            
            # Convert to MatchResult objects
            from app.services.matcher import MatchResult
            match_objects = [
                MatchResult(
                    kb_item_id=m['kb_item_id'],
                    content=m['matched_content'],
                    score=m['match_percentage'] / 100,
                    rank=m['rank']
                )
                for m in matches
            ]
            
            # Compose response
            composed = await composer.compose(
                requirement=req['requirement_text'],
                matches=match_objects,
                style=response_style,
                mode=mode,
                tone=tone,
                priority=req.get('priority', 'Optional'),
                company_profile=company_profile,
                past_performance=past_performance,
                team_profiles=team_profiles
            )
            
            # Check if response already exists for this requirement
            existing_resp = supabase.table('responses')\
                .select('id, version')\
                .eq('document_id', document_id)\
                .eq('requirement_id', req['id'])\
                .execute()
            
            print(f"[SAVE] Composed text length: {len(composed.text)} chars")
            
            if existing_resp.data and len(existing_resp.data) > 0:
                # UPDATE existing response
                existing = existing_resp.data[0]
                supabase.table('responses').update({
                    'response_text': composed.text,
                    'version': existing['version'] + 1,
                }).eq('id', existing['id']).execute()
            else:
                # INSERT new response
                resp_result = supabase.table('responses').insert({
                    'document_id': document_id,
                    'requirement_id': req['id'],
                    'response_text': composed.text,
                    'status': 'DRAFT',
                    'version': 1,
                    'created_by': user_id,
                    'tenant_id': tenant_id
                }).execute()
                
                # Log AI percentage internally
                if composed.ai_percentage > 0 and resp_result.data:
                    try:
                        supabase.table('ai_percentage_log').insert({
                            'response_id': resp_result.data[0]['id'],
                            'total_tokens': len(composed.text.split()),
                            'kb_tokens': int(len(composed.text.split()) * composed.kb_percentage / 100),
                            'ai_tokens': int(len(composed.text.split()) * composed.ai_percentage / 100),
                            'ai_percentage': composed.ai_percentage,
                            'gate_passed': composed.ai_percentage < 30,
                        }).execute()
                    except Exception as e:
                        print(f"[WARN] Failed to log AI percentage: {e}")
                        
        except Exception as e:
            print(f"[ERROR] Failed to generate response for requirement {req['id']}: {e}")
            continue
    
    print(f"[DONE] Generated responses for {len(requirements)} requirements")


@router.put("/responses/{response_id}", response_model=ResponseResponse)
async def update_response(
    response_id: str,
    update: ResponseUpdate,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Update response text."""
    
    # Get response and verify access
    # Get response and verify access
    # RLS handles tenant isolation, but we verify ownership logic
    resp_result = supabase.table('responses')\
        .select('*, documents!inner(user_id, tenant_id)')\
        .eq('id', response_id)\
        .single()\
        .execute()
    
    if not resp_result.data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if user.get('tenant_id'):
        if resp_result.data['documents'].get('tenant_id') != user['tenant_id']:
            raise HTTPException(status_code=403, detail="Access denied")
    elif resp_result.data['documents']['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if resp_result.data['status'] not in ['DRAFT', 'PENDING_REVIEW']:
        raise HTTPException(status_code=400, detail="Cannot edit approved response")
    
    # Role Check: Auditor cannot edit
    if user.get('role') == 'AUDITOR':
        raise HTTPException(status_code=403, detail="Auditors have read-only access")
    
    # Update
    update_data = {}
    if update.response_text is not None:
        update_data['response_text'] = update.response_text
        update_data['version'] = resp_result.data['version'] + 1
    
    update_data['updated_at'] = datetime.now().isoformat()
    
    result = supabase.table('responses')\
        .update(update_data)\
        .eq('id', response_id)\
        .execute()
    
    return result.data[0]


@router.post("/responses/{response_id}/submit")
async def submit_for_review(
    response_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Submit response for review."""
    
    # Verify access
    # Verify access
    resp_result = supabase.table('responses')\
        .select('*, documents!inner(user_id, tenant_id)')\
        .eq('id', response_id)\
        .single()\
        .execute()
    
    if not resp_result.data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if user.get('tenant_id'):
        if resp_result.data['documents'].get('tenant_id') != user['tenant_id']:
            raise HTTPException(status_code=403, detail="Access denied")
    elif resp_result.data['documents']['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if resp_result.data['status'] != 'DRAFT':
        raise HTTPException(status_code=400, detail="Response already submitted")
    
    # Role Check: Auditor cannot submit
    if user.get('role') == 'AUDITOR':
        raise HTTPException(status_code=403, detail="Auditors cannot submit responses")
    
    # Update status
    result = supabase.table('responses')\
        .update({
            'status': 'PENDING_REVIEW',
            'updated_at': datetime.now().isoformat()
        })\
        .eq('id', response_id)\
        .execute()
    
    # Log workflow history
    supabase.table('workflow_history').insert({
        'entity_type': 'response',
        'entity_id': response_id,
        'tenant_id': user.get('tenant_id'),
        'old_status': resp_result.data['status'],
        'new_status': 'PENDING_REVIEW',
        'changed_by': user['id'],
        'change_reason': 'Submitted for review'
    }).execute()
    
    return {"message": "Submitted for review", "response": result.data[0]}


@router.post("/responses/{response_id}/approve")
async def approve_response(
    response_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Approve response."""
    
    # Verify access (in production, check for reviewer role)
    resp_result = supabase.table('responses')\
        .select('*, documents!inner(user_id)')\
        .eq('id', response_id)\
        .single()\
        .execute()
    
    if not resp_result.data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if resp_result.data['status'] not in ['DRAFT', 'PENDING_REVIEW']:
        raise HTTPException(status_code=400, detail="Response already processed")
    
    # Role Check: Only Admin or Manager can approve
    user_role = user.get('role', 'USER')
    if user_role not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Only Managers or Admins can approve responses")
    
    # Approve
    result = supabase.table('responses')\
        .update({
            'status': 'APPROVED',
            'approved_by': user['id'],
            'approved_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })\
        .eq('id', response_id)\
        .execute()
        
    # Log workflow history
    supabase.table('workflow_history').insert({
        'entity_type': 'response',
        'entity_id': response_id,
        'tenant_id': user.get('tenant_id'),
        'old_status': resp_result.data['status'],
        'new_status': 'APPROVED',
        'changed_by': user['id'],
        'change_reason': 'Approved by reviewer'
    }).execute()
    
    return {"message": "Response approved", "response": result.data[0]}


# --- Review Comments ---

@router.get("/responses/{response_id}/comments")
async def get_response_comments(
    response_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Get comments for a response."""
    result = supabase.table('review_comments')\
        .select('*')\
        .eq('response_id', response_id)\
        .order('created_at')\
        .execute()
    return result.data

@router.post("/responses/{response_id}/comments")
async def add_response_comment(
    response_id: str,
    comment_data: dict,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Add a comment to a response."""
    result = supabase.table('review_comments').insert({
        'response_id': response_id,
        'user_id': user['id'],
        'tenant_id': user.get('tenant_id'),
        'comment_text': comment_data.get('comment_text'),
        'resolved': False
    }).execute()
    return result.data[0]

@router.post("/responses/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Resolve a comment."""
    result = supabase.table('review_comments')\
        .update({'resolved': True})\
        .eq('id', comment_id)\
        .execute()
    return result.data[0]
@router.delete("/responses/{response_id}")
async def delete_response(
    response_id: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Delete a response."""
    # Verify access
    resp_result = supabase.table('responses')\
        .select('*, documents!inner(user_id, tenant_id)')\
        .eq('id', response_id)\
        .single()\
        .execute()
    
    if not resp_result.data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if user.get('tenant_id'):
        if resp_result.data['documents'].get('tenant_id') != user['tenant_id']:
            raise HTTPException(status_code=403, detail="Access denied")
    elif resp_result.data['documents']['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete match results first (due to FK)
    supabase.table('match_results').delete().eq('requirement_id', resp_result.data['requirement_id']).execute()
    
    # Delete AI logs
    supabase.table('ai_percentage_log').delete().eq('response_id', response_id).execute()
    
    # Delete comments
    supabase.table('review_comments').delete().eq('response_id', response_id).execute()
    
    # Delete the response
    supabase.table('responses').delete().eq('id', response_id).execute()
    
    return {"status": "success", "message": "Response deleted"}
