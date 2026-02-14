// API service for humanization
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface HumanizeOptions {
    maxAiPercentage?: number
    maxAttempts?: number
    style?: 'professional' | 'casual' | 'formal' | 'simple' | 'academic'
    mode?: 'light' | 'balanced' | 'aggressive' | 'creative'
}

export interface HumanizeResponse {
    humanizedText: string
    originalAiScore: number
    humanizedAiScore: number
    reduction: number
}

export const humanizeDocument = async (file: File | null, text?: string, options: HumanizeOptions = {}): Promise<HumanizeResponse> => {
    const formData = new FormData()
    if (file) formData.append('file', file)
    if (text) formData.append('text', text)

    // Add options
    if (options.maxAiPercentage !== undefined) formData.append('max_ai_percentage', options.maxAiPercentage.toString())
    if (options.maxAttempts !== undefined) formData.append('max_attempts', options.maxAttempts.toString())
    if (options.style) formData.append('style', options.style)
    if (options.mode) formData.append('mode', options.mode)

    const response = await fetch(`${API_BASE_URL}/humanizer`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        throw new Error('Failed to humanize document')
    }

    const data = await response.json()

    return {
        humanizedText: data.transformed || data.humanized_text || '',
        originalAiScore: data.original_score || data.original_ai_percentage || 0,
        humanizedAiScore: data.new_score || data.final_ai_percentage || 0,
        reduction: typeof data.reduction === 'string' ? parseFloat(data.reduction) : (data.reduction || 0)
    }
}

// Extract text from file
export const extractTextFromFile = async (file: File): Promise<string> => {
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (extension === 'txt') {
        return await file.text()
    }

    // For PDF and DOCX, we'll send to backend for extraction
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/extract-text`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        throw new Error('Failed to extract text from document')
    }

    const data = await response.json()
    return data.text
}

// Validate file
export const validateFile = (file: File): { valid: boolean; error?: string } => {
    const validTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
    ]

    const validExtensions = ['pdf', 'doc', 'docx', 'txt']
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (!validTypes.includes(file.type) && !validExtensions.includes(extension || '')) {
        return { valid: false, error: 'fileType' }
    }

    // 10MB limit
    if (file.size > 10 * 1024 * 1024) {
        return { valid: false, error: 'fileSize' }
    }

    return { valid: true }
}
