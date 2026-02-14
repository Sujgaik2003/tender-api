'use client';

import { useLanguageStore } from '@/store/use-language-store';
import { translations, TranslationKeys } from './translations';

export function useI18n() {
    const { language } = useLanguageStore();

    const t = (key: TranslationKeys): string => {
        return translations[language][key] || translations['en'][key] || key;
    };

    return { t, language };
}
