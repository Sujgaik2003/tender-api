import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatDate(date: string | Date): string {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

export function formatDateTime(date: string | Date): string {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

export function getMatchColor(percentage: number): string {
    if (percentage >= 80) return 'match-excellent';
    if (percentage >= 60) return 'match-good';
    if (percentage >= 40) return 'match-fair';
    return 'match-poor';
}

export function getMatchBgColor(percentage: number): string {
    if (percentage >= 80) return 'bg-emerald-500';
    if (percentage >= 60) return 'bg-primary-500';
    if (percentage >= 40) return 'bg-amber-500';
    return 'bg-red-500';
}

export function getStatusBadgeClass(status: string): string {
    switch (status) {
        case 'READY':
        case 'APPROVED':
            return 'badge-success';
        case 'PARSING':
        case 'EXTRACTING':
        case 'MATCHING':
        case 'PENDING_REVIEW':
            return 'badge-warning';
        case 'ERROR':
            return 'badge-error';
        default:
            return 'badge-neutral';
    }
}

export function getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
        UPLOADED: 'uploaded',
        PARSING: 'parsing',
        EXTRACTING: 'extracting',
        MATCHING: 'matching',
        READY: 'ready',
        ERROR: 'error',
        DRAFT: 'draft',
        PENDING_REVIEW: 'underReview',
        APPROVED: 'approved',
        EXPORTED: 'exported',
    };
    return labels[status] || status.toLowerCase();
}

export function getCategoryLabel(category: string): string {
    const labels: Record<string, string> = {
        ELIGIBILITY: 'eligibility',
        TECHNICAL: 'technical',
        COMPLIANCE: 'compliance',
    };
    return labels[category] || category.toLowerCase();
}

export function getCategoryColor(category: string): string {
    const colors: Record<string, string> = {
        ELIGIBILITY: 'bg-purple-100 text-purple-800',
        TECHNICAL: 'bg-blue-100 text-blue-800',
        COMPLIANCE: 'bg-teal-100 text-teal-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
}

export function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

export function generateId(): string {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
}
