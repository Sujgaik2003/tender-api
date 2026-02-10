import sys
import time
import traceback
import asyncio
from celery import shared_task
from app.core.celery_app import celery_app
from app.core.supabase import get_supabase
from app.services.pipeline import process_document

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Using shared_task decorator allows this function to be used by any Celery app
# (useful if we have multiple apps, though here we have one)

@shared_task(bind=True, max_retries=3, soft_time_limit=3600)  # 1 hour limit for huge files
def parse_document_task(self, document_id: str):
    """
    Background worker task to parse a document.
    Replaces the previous synchronous background_tasks logic.
    """
    print(f"[WORKER] Starting parse task for document {document_id}")
    
    # Celery runs in a separate thread/process, so we need a new event loop for async code
    try:
        # Check if we have an event loop
        loop = asyncio.get_event_loop()
        # If loop is closed, create new one
        if loop.is_closed():
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)
    except RuntimeError:
        # If no loop in this thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        # Execute the pipeline
        # Note: process_document is an async function (from pipeline.py)
        result = loop.run_until_complete(process_document(document_id))
        
        print(f"[WORKER] Successfully parsed document {document_id}")
        return {
            "status": "success", 
            "document_id": document_id
        }
        
    except Exception as e:
        print(f"[WORKER] FAILED to parse document {document_id}: {e}")
        traceback.print_exc()
        
        # Update status in DB to ERROR
        supabase = get_supabase()
        supabase.table('documents').update({
            'status': 'ERROR',
            'error_message': f"Worker processing failed: {str(e)}"
        }).eq('id', document_id).execute()
        
        # Retry logic
        try:
            self.retry(exc=e, countdown=60)  # Retry after 1 minute
        except Exception:
            pass # Max retries exceeded
            
        return {
            "status": "error",
            "error": str(e)
        }
        
@shared_task(bind=True, max_retries=2)
def discovery_scan_task(self, tenant_id: str):
    """
    Background worker task to scan for new tenders.
    """
    from app.services.discovery.scanner import DiscoveryScanner
    from app.services.discovery.scrapers.gem_scraper import GeMScraper
    
    print(f"[WORKER] Starting discovery scan for tenant {tenant_id}")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        scanner = DiscoveryScanner(tenant_id)
        scrapers = [GeMScraper()]
        result = loop.run_until_complete(scanner.run_discovery(scrapers))
        
        print(f"[WORKER] Successfully completed discovery scan for tenant {tenant_id}: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"[WORKER] FAILED discovery scan for tenant {tenant_id}: {e}")
        traceback.print_exc()
        return {"status": "error", "error": str(e)}
