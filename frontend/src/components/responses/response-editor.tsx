'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/input';
import {
    Save,
    Check,
    Send,
    RotateCcw,
    RefreshCw,
    ChevronDown,
    ChevronUp,
    Sparkles,
    MessageSquare,
    UserCircle,
    Trash2
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import toast from 'react-hot-toast';
import { cn, getStatusLabel, getCategoryLabel, getCategoryColor } from '@/lib/utils';
import type { Response, Requirement, ReviewComment } from '@/types';

import { useI18n } from '@/lib/i18n';

interface ResponseEditorProps {
    response: Response;
    requirement?: Requirement;
    onSave: (text: string) => Promise<void>;
    onSubmit: () => Promise<void>;
    onApprove?: () => Promise<void>;
    onRegenerate?: (mode: string, tone: string) => Promise<void>;
    onDelete?: () => Promise<void>;
    canApprove?: boolean;
    readOnly?: boolean;
}

export function ResponseEditor({
    response,
    requirement,
    onSave,
    onSubmit,
    onApprove,
    onRegenerate,
    onDelete,
    canApprove = false,
    readOnly = false,
}: ResponseEditorProps) {
    const { t, language } = useI18n();
    const [text, setText] = useState(response.response_text);
    const [isExpanded, setIsExpanded] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [isRegenerating, setIsRegenerating] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);
    const [mode, setMode] = useState('balanced');
    const [tone, setTone] = useState('professional');
    const [isHumanizing, setIsHumanizing] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // Comment states
    const [comments, setComments] = useState<ReviewComment[]>([]);
    const [newComment, setNewComment] = useState("");
    const [isLoadingComments, setIsLoadingComments] = useState(false);
    const [isAddingComment, setIsAddingComment] = useState(false);

    useEffect(() => {
        if (isExpanded) {
            fetchComments();
        }
    }, [isExpanded, response.id]);

    const fetchComments = async () => {
        setIsLoadingComments(true);
        try {
            const data = await apiClient.getResponseComments(response.id);
            setComments(data);
        } catch (e) {
            console.error("Failed to load comments");
        } finally {
            setIsLoadingComments(false);
        }
    };

    const handleAddComment = async () => {
        if (!newComment.trim()) return;
        setIsAddingComment(true);
        try {
            const added = await apiClient.addResponseComment(response.id, newComment);
            setComments([...comments, added]);
            setNewComment("");
            toast.success("Comment added");
        } catch (e) {
            toast.error("Failed to add comment");
        } finally {
            setIsAddingComment(false);
        }
    };

    const handleResolveComment = async (id: string) => {
        try {
            await apiClient.resolveComment(id);
            setComments(comments.map(c => c.id === id ? { ...c, resolved: true } : c));
            toast.success("Comment resolved");
        } catch (e) {
            toast.error("Failed to resolve");
        }
    };

    const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(e.target.value);
        setHasChanges(e.target.value !== response.response_text);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await onSave(text);
            setHasChanges(false);
            toast.success(t('save'));
        } finally {
            setIsSaving(false);
        }
    };

    const handleRegenerate = async () => {
        if (!onRegenerate) return;
        setIsRegenerating(true);
        try {
            await onRegenerate(mode, tone);
        } finally {
            setIsRegenerating(false);
        }
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            if (hasChanges) await onSave(text);
            await onSubmit();
            toast.success(t('submit'));
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleApprove = async () => {
        if (!onApprove) return;
        setIsApproving(true);
        try {
            await onApprove();
            toast.success("Approved");
        } finally {
            setIsApproving(false);
        }
    };

    const handleReset = () => {
        setText(response.response_text);
        setHasChanges(false);
    };

    const handleDelete = async () => {
        if (!onDelete) return;
        if (!window.confirm("Are you sure you want to delete this response?")) return;

        setIsDeleting(true);
        try {
            await onDelete();
        } finally {
            setIsDeleting(false);
        }
    };

    const handleHumanizeOnly = async () => {
        if (!text || text.length < 10) {
            toast.error("Text too short to humanize");
            return;
        }

        setIsHumanizing(true);
        try {
            const result = await apiClient.humanize(text, { mode, style: tone });
            if (result.transformed) {
                setText(result.transformed);
                setHasChanges(true);
                toast.success("Content humanized!");
            }
        } catch (error: any) {
            toast.error(error.message || "Failed to humanize");
        } finally {
            setIsHumanizing(false);
        }
    };

    React.useEffect(() => {
        if (!hasChanges) {
            setText(response.response_text);
        }
    }, [response.response_text, hasChanges]);

    const isEditable = !readOnly && (response.status === 'DRAFT' || response.status === 'PENDING_REVIEW');
    const statusVariant = response.status === 'APPROVED' ? 'success'
        : response.status === 'PENDING_REVIEW' ? 'warning'
            : 'neutral';

    const isRtl = language === 'ar';

    return (
        <Card padding="none" className="overflow-hidden border-surface-200 shadow-lg shadow-slate-200/40 rounded-2xl">
            {/* Header */}
            <div
                className={cn(
                    "p-5 border-b border-surface-200 cursor-pointer hover:bg-slate-50/50 transition-colors flex items-center justify-between",
                    isRtl && "flex-row-reverse text-right"
                )}
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className={cn("flex items-center gap-4 min-w-0", isRtl && "flex-row-reverse text-right")}>
                    {requirement && (
                        <Badge className={getCategoryColor(requirement.category)}>
                            {getCategoryLabel(requirement.category)}
                        </Badge>
                    )}
                    <span className="font-bold text-slate-800 break-words leading-snug">
                        {requirement?.requirement_text || 'General Response'}
                    </span>
                    {requirement?.priority === 'Mandatory' && (
                        <Badge className="bg-red-50 text-red-600 border-red-100 font-black text-[10px] uppercase tracking-tighter">Required</Badge>
                    )}
                </div>
                <div className={cn("flex items-center gap-3", isRtl && "flex-row-reverse")}>
                    <Badge variant={statusVariant} className="px-3 py-1 rounded-lg">
                        {getStatusLabel(response.status)}
                    </Badge>
                    {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-surface-400" />
                    ) : (
                        <ChevronDown className="w-5 h-5 text-surface-400" />
                    )}
                </div>
            </div>

            {/* Editor Content */}
            {isExpanded && (
                <div className="p-6 space-y-6 animate-in fade-in duration-300">
                    <Textarea
                        value={text}
                        onChange={handleTextChange}
                        disabled={!isEditable}
                        className={cn(
                            'min-h-[250px] font-medium text-slate-700 resize-none focus:ring-4 focus:ring-primary-500/5 border-slate-100 rounded-2xl transition-all leading-relaxed',
                            !isEditable && 'bg-slate-50/50 cursor-not-allowed',
                            isRtl && "text-right"
                        )}
                        dir={isRtl ? 'rtl' : 'ltr'}
                        placeholder="Response content..."
                    />

                    {/* Controls Footer */}
                    <div className={cn(
                        "flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-slate-100",
                        isRtl && "flex-row-reverse"
                    )}>
                        <div className={cn("flex flex-wrap items-center gap-3", isRtl && "flex-row-reverse")}>
                            {isEditable && onRegenerate && (
                                <div className="flex items-center bg-white p-1 rounded-2xl border border-slate-200 shadow-sm hover:border-primary-100 transition-all">
                                    <div className="flex flex-col px-4 border-r border-slate-100 py-1">
                                        <span className="text-[9px] uppercase font-black text-slate-400 tracking-widest mb-0.5">{t('mode')}</span>
                                        <select
                                            value={mode}
                                            onChange={(e) => setMode(e.target.value)}
                                            className="text-xs font-black bg-transparent border-none p-0 focus:ring-0 text-slate-700 cursor-pointer"
                                        >
                                            <option value="balanced">Balanced</option>
                                            <option value="aggressive">Sales-Focused</option>
                                            <option value="creative">Creative</option>
                                        </select>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={handleRegenerate}
                                        isLoading={isRegenerating}
                                        disabled={hasChanges}
                                        className="h-9 px-5 rounded-xl ml-1.5 font-black shadow-md shadow-primary-500/20 active:scale-95 transition-transform"
                                    >
                                        <RefreshCw className="w-3.5 h-3.5 mr-2" />
                                        Update AI
                                    </Button>
                                </div>
                            )}

                            {isEditable && (
                                <Button
                                    variant="secondary"
                                    onClick={handleHumanizeOnly}
                                    isLoading={isHumanizing}
                                    className="h-10 rounded-xl border-dashed border-primary-200 text-primary-600 font-bold"
                                >
                                    <Sparkles className="w-4 h-4 mr-2" />
                                    {t('humanize')}
                                </Button>
                            )}
                        </div>

                        <div className="flex items-center gap-3">
                            {isEditable && (
                                <>
                                    <Button variant="secondary" onClick={handleSave} isLoading={isSaving} disabled={!hasChanges} title={t('save')} className="h-10 px-4 rounded-xl">
                                        <Save className="w-4 h-4" />
                                    </Button>

                                    {response.status === 'DRAFT' && (
                                        <Button onClick={handleSubmit} isLoading={isSubmitting} className="h-10 px-6 rounded-xl font-black bg-slate-900 shadow-xl shadow-slate-900/10">
                                            <Send className="w-4 h-4 mr-2" />
                                            Submit
                                        </Button>
                                    )}
                                </>
                            )}

                            {canApprove && response.status === 'PENDING_REVIEW' && (
                                <Button onClick={handleApprove} isLoading={isApproving} className="h-10 px-8 rounded-xl font-black bg-emerald-600 hover:bg-emerald-700 shadow-xl shadow-emerald-500/20">
                                    <Check className="w-4 h-4 mr-2" />
                                    Approve Final
                                </Button>
                            )}

                            {!readOnly && onDelete && (
                                <Button
                                    variant="secondary"
                                    onClick={handleDelete}
                                    isLoading={isDeleting}
                                    className="h-10 w-10 p-0 rounded-xl border-red-100 text-red-500 hover:bg-red-50"
                                    title="Delete Response"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Review Comments Section */}
                    <div className="mt-8 pt-8 border-t-2 border-slate-100 bg-slate-50/20 -mx-6 px-6 pb-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="bg-slate-100 p-2 rounded-xl">
                                <MessageSquare className="w-4 h-4 text-slate-500" />
                            </div>
                            <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Internal Review Feed</h3>
                        </div>

                        <div className="space-y-4 mb-6 max-h-[300px] overflow-y-auto pr-2">
                            {comments.map((comment) => (
                                <div key={comment.id} className={cn(
                                    "p-4 rounded-2xl border transition-all animate-in slide-in-from-left-2",
                                    comment.resolved
                                        ? "bg-slate-50 border-slate-100 opacity-50"
                                        : "bg-white border-primary-50 shadow-sm"
                                )}>
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            <UserCircle className="w-4 h-4 text-slate-300" />
                                            <span className="text-xs font-black text-slate-700">Audit Reviewer #{(comment.id.slice(0, 4))}</span>
                                        </div>
                                        {!comment.resolved && (
                                            <button
                                                onClick={() => handleResolveComment(comment.id)}
                                                className="text-[10px] font-black uppercase text-primary-600 hover:bg-primary-50 px-2 py-1 rounded-lg transition-colors"
                                            >
                                                Mark Resolved
                                            </button>
                                        )}
                                    </div>
                                    <p className="text-sm text-slate-600 leading-relaxed font-medium">{comment.comment_text}</p>
                                </div>
                            ))}
                            {comments.length === 0 && !isLoadingComments && (
                                <div className="text-center py-6 border-2 border-dashed border-slate-100 rounded-3xl">
                                    <p className="text-xs text-slate-400 font-bold">No feedback yet. Ready for first pass.</p>
                                </div>
                            )}
                        </div>

                        <div className="flex gap-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm focus-within:ring-4 focus-within:ring-primary-500/5 transition-all">
                            <input
                                value={newComment}
                                onChange={(e) => setNewComment(e.target.value)}
                                placeholder="Add revision notes..."
                                className="flex-1 bg-transparent px-4 py-2 text-sm outline-none font-medium"
                                onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                            />
                            <Button
                                size="sm"
                                onClick={handleAddComment}
                                isLoading={isAddingComment}
                                disabled={!newComment.trim()}
                                className="rounded-xl px-4 py-2 font-black h-10"
                            >
                                Feedback
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </Card>
    );
}

interface ResponseListProps {
    responses: Response[];
    requirements: Requirement[];
    onSave: (id: string, text: string) => Promise<void>;
    onSubmit: (id: string) => Promise<void>;
    onApprove?: (id: string) => Promise<void>;
    onRegenerate?: (requirementId: string, mode: string, tone: string) => Promise<void>;
    onDelete?: (id: string) => Promise<void>;
    canApprove?: boolean;
    readOnly?: boolean;
}

export function ResponseList({
    responses,
    requirements,
    onSave,
    onSubmit,
    onApprove,
    onRegenerate,
    onDelete,
    canApprove = false,
    readOnly = false,
}: ResponseListProps) {
    const getRequirement = (requirementId: string | null) => {
        if (!requirementId) return undefined;
        return requirements.find((r) => r.id === requirementId);
    };

    return (
        <div className="space-y-6">
            {responses.map((response) => (
                <ResponseEditor
                    key={`${response.id}-v${response.version}`}
                    response={response}
                    requirement={getRequirement(response.requirement_id)}
                    onSave={(text) => onSave(response.id, text)}
                    onSubmit={() => onSubmit(response.id)}
                    onApprove={onApprove ? () => onApprove(response.id) : undefined}
                    onRegenerate={onRegenerate ? (mode, tone) => onRegenerate(response.requirement_id!, mode, tone) : undefined}
                    onDelete={onDelete ? () => onDelete(response.id) : undefined}
                    canApprove={canApprove}
                    readOnly={readOnly}
                />
            ))}
        </div>
    );
}
