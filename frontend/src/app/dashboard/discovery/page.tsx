'use client';

import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { createClient } from '@/lib/supabase/client';
import {
    Search,
    Zap,
    RefreshCcw,
    ExternalLink,
    CheckCircle2,
    XCircle,
    FileText,
    MapPin,
    Calendar,
    Filter,
    ArrowUpRight,
    TrendingUp,
    ShieldCheck,
    Trash2
} from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import { useI18n } from '@/lib/i18n';
import toast from 'react-hot-toast';

interface Tender {
    id: string;
    external_ref_id: string;
    title: string;
    authority: string;
    publish_date: string;
    submission_deadline: string;
    category: string;
    source_portal: string;
    match_score: number;
    match_explanation: string;
    domain_tags: string[];
    status: 'PENDING' | 'APPROVED' | 'REJECTED';
    tender_attachments?: { file_name: string; external_url: string }[];
}

export default function DiscoveryPage() {
    const { t, language } = useI18n();
    const supabase = createClient();
    const [loading, setLoading] = useState(true);
    const [scanning, setScanning] = useState(false);
    const [tenders, setTenders] = useState<Tender[]>([]);
    const [filter, setFilter] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
    const [tenantId, setTenantId] = useState<string | null>(null);

    useEffect(() => {
        loadTenders();
    }, [filter]);

    const loadTenders = async () => {
        setLoading(true);
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Get tenant_id from user_profile
            const { data: profile } = await supabase
                .from('user_profiles')
                .select('tenant_id')
                .eq('id', user.id)
                .single<{ tenant_id: string }>();

            if (profile?.tenant_id) {
                setTenantId(profile.tenant_id);
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/discovery/tenders?tenant_id=${profile.tenant_id}&status=${filter}`);
                const data = await response.json();
                setTenders(data);
            }
        } catch (error) {
            console.error('Error loading tenders:', error);
            toast.error('Failed to load tenders');
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        if (!tenantId) return;
        setScanning(true);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/discovery/scan?tenant_id=${tenantId}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Scan failed to start');

            toast.success('Pilot sync started in background');

            // Wait 10 seconds and refresh leads (gives the worker time to save first few)
            setTimeout(() => {
                loadTenders();
                setScanning(false);
            }, 10000);

        } catch (error) {
            console.error('Error scanning:', error);
            toast.error('Failed to start sync');
            setScanning(false);
        }
    };

    const handleAction = async (tenderId: string, action: 'approve' | 'reject') => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/discovery/tenders/${tenderId}/${action}`, {
                method: 'POST'
            });
            if (response.ok) {
                toast.success(`Tender ${action === 'approve' ? 'approved' : 'rejected'}`);
                setTenders(prev => prev.filter(t => t.id !== tenderId));
            }
        } catch (error) {
            toast.error(`Failed to ${action} tender`);
        }
    };

    const handleDelete = async (tenderId: string) => {
        if (!confirm('Are you sure you want to permanently delete this tender?')) return;

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/discovery/tenders/${tenderId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                toast.success('Tender deleted permanently');
                setTenders(prev => prev.filter(t => t.id !== tenderId));
            } else {
                throw new Error('Failed to delete');
            }
        } catch (error) {
            toast.error('Failed to delete tender');
        }
    };

    const isRtl = language === 'ar';

    return (
        <DashboardLayout
            title="Tender Discovery"
            subtitle="Autonomous agent scanning global portals for high-match opportunities."
        >
            {/* Header / Stats */}
            <div className="flex flex-col md:flex-row gap-6 mb-8 items-start justify-between">
                <div className="flex gap-4">
                    <Card className="p-4 bg-white border-primary-100 flex items-center gap-4 shadow-sm min-w-[200px]">
                        <div className="p-2 bg-primary-50 rounded-lg">
                            <Zap className="w-5 h-5 text-primary-600" />
                        </div>
                        <div>
                            <p className="text-2xl font-black text-surface-900">{tenders.length}</p>
                            <p className="text-[10px] font-bold text-surface-400 uppercase tracking-widest">Active Leads</p>
                        </div>
                    </Card>
                </div>

                <div className="flex gap-3 w-full md:w-auto">
                    <div className="flex bg-surface-100 p-1 rounded-xl gap-1">
                        {(['PENDING', 'APPROVED', 'REJECTED'] as const).map((s) => (
                            <button
                                key={s}
                                onClick={() => setFilter(s)}
                                className={cn(
                                    "px-4 py-1.5 rounded-lg text-xs font-bold transition-all",
                                    filter === s ? "bg-white text-surface-900 shadow-sm" : "text-surface-500 hover:text-surface-700"
                                )}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                    <Button
                        onClick={handleScan}
                        disabled={scanning}
                        className="rounded-xl font-bold bg-primary-600 hover:bg-primary-700 shadow-lg shadow-primary-500/20"
                        leftIcon={<RefreshCcw className={cn("w-4 h-4", scanning && "animate-spin")} />}
                    >
                        {scanning ? "Scanning..." : "Sync Portals"}
                    </Button>
                </div>
            </div>

            {/* Leads Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {loading ? (
                    [...Array(4)].map((_, i) => (
                        <Card key={i} className="p-6">
                            <Skeleton className="h-6 w-3/4 mb-4" />
                            <Skeleton className="h-4 w-1/2 mb-6" />
                            <div className="flex gap-2">
                                <Skeleton className="h-8 w-20" />
                                <Skeleton className="h-8 w-20" />
                            </div>
                        </Card>
                    ))
                ) : tenders.length === 0 ? (
                    <div className="col-span-full py-20 text-center">
                        <div className="w-20 h-20 bg-surface-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-surface-100">
                            <Search className="w-10 h-10 text-surface-300" />
                        </div>
                        <h3 className="text-xl font-bold text-surface-900">No tenders discovered yet</h3>
                        <p className="text-surface-500 mb-6">Trigger a sync to scan configured portals for opportunities.</p>
                        <Button onClick={handleScan} variant="secondary" className="rounded-xl">Start Pilot Sync</Button>
                    </div>
                ) : (
                    tenders.map((tender) => (
                        <Card key={tender.id} className="group relative overflow-hidden bg-white border-surface-100 hover:shadow-xl hover:border-primary-100 transition-all duration-300 p-6">
                            {/* Score Badge */}
                            <div className="absolute top-0 right-0 p-4">
                                <div className={cn(
                                    "px-3 py-1.5 rounded-xl border flex items-center gap-1.5 transition-transform group-hover:scale-105",
                                    tender.match_score > 70 ? "bg-emerald-50 border-emerald-100 text-emerald-700" :
                                        tender.match_score > 40 ? "bg-amber-50 border-amber-100 text-amber-700" :
                                            "bg-surface-50 border-surface-100 text-surface-700"
                                )}>
                                    <TrendingUp className="w-3.5 h-3.5" />
                                    <span className="text-sm font-black">{Math.round(tender.match_score)}% Match</span>
                                </div>
                            </div>

                            {/* Main Content */}
                            <div className="mb-4">
                                <div className="flex items-center gap-2 text-primary-600 mb-2">
                                    <ShieldCheck className="w-4 h-4" />
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">{tender.source_portal}</span>
                                </div>
                                <h3 className="line-clamp-2 text-lg font-black text-surface-900 leading-tight mb-2 group-hover:text-primary-600 transition-colors">
                                    {tender.title}
                                </h3>
                                <div className="flex flex-wrap gap-2 mb-4">
                                    {tender.domain_tags.map(tag => (
                                        <Badge key={tag} variant="info" className="bg-surface-50 text-surface-600 border-none font-bold text-[10px] uppercase">
                                            {tag}
                                        </Badge>
                                    ))}
                                </div>
                            </div>

                            {/* Details Row */}
                            <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-surface-50 rounded-2xl border border-surface-100">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 text-surface-400">
                                        <Calendar className="w-3.5 h-3.5" />
                                        <span className="text-[10px] font-bold uppercase">Deadline</span>
                                    </div>
                                    <p className="text-xs font-black text-surface-700">{formatDate(tender.submission_deadline)}</p>
                                </div>
                                <div className="space-y-1 text-right">
                                    <div className="flex items-center gap-1.5 text-surface-400 justify-end">
                                        <MapPin className="w-3.5 h-3.5" />
                                        <span className="text-[10px] font-bold uppercase">Authority</span>
                                    </div>
                                    <p className="text-xs font-black text-surface-700 truncate max-w-[150px] ml-auto">{tender.authority}</p>
                                </div>
                            </div>

                            {/* AI Explanation */}
                            <div className="mb-6">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
                                    <span className="text-[10px] font-black text-surface-400 uppercase tracking-widest">AI Matching Insights</span>
                                </div>
                                <p className="text-xs text-surface-600 font-medium leading-relaxed bg-primary-50/30 p-3 rounded-xl border border-primary-50">
                                    {tender.match_explanation}
                                </p>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center justify-between mt-auto pt-4 border-t border-surface-100">
                                <div className="flex gap-2">
                                    {tender.tender_attachments?.slice(0, 2).map((att, i) => (
                                        <a key={i} href={att.external_url} target="_blank" rel="noreferrer" className="p-2 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors">
                                            <FileText className="w-4 h-4 text-surface-400" />
                                        </a>
                                    ))}
                                </div>

                                {filter === 'PENDING' ? (
                                    <div className="flex gap-2">
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            className="rounded-lg border border-surface-200 text-surface-600 hover:text-red-600 hover:bg-red-50"
                                            onClick={() => handleAction(tender.id, 'reject')}
                                        >
                                            <XCircle className="w-4 h-4 mr-1.5" /> Reject
                                        </Button>
                                        <Button
                                            size="sm"
                                            className="rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20"
                                            onClick={() => handleAction(tender.id, 'approve')}
                                        >
                                            <CheckCircle2 className="w-4 h-4 mr-1.5" /> Approve for Bid
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-3">
                                        <Badge className={cn(
                                            "rounded-lg font-black uppercase tracking-widest text-[10px] px-3 py-1.5",
                                            filter === 'APPROVED' ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                                        )}>
                                            {filter}
                                        </Badge>
                                        {filter === 'REJECTED' && (
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                className="h-8 w-8 p-0 text-surface-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                                                onClick={() => handleDelete(tender.id)}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </DashboardLayout>
    );
}
