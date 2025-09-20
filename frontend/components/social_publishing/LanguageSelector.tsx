'use client'

import { Checkbox } from '@/components/ui';
import { LanguageSelectorProps } from '@/types/social_publishing';

const SUPPORTED_LANGUAGES = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
    { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
    { code: 'te', name: 'Telugu', flag: '🇮🇳' },
    { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
    { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
    { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
    { code: 'ml', name: 'Malayalam', flag: '🇮🇳' }
];

export default function LanguageSelector({
    selectedLanguages,
    onLanguageChange,
    onLanguageAdded,
    loadingStates
}: LanguageSelectorProps) {

    const handleLanguageToggle = (languageCode: string, checked: boolean) => {
        if (checked) {
            const newLanguages = [...selectedLanguages, languageCode];
            onLanguageChange(newLanguages);
            onLanguageAdded(languageCode);
        } else {
            const newLanguages = selectedLanguages.filter(lang => lang !== languageCode);
            onLanguageChange(newLanguages);
        }
    };

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-3">
                    Select Languages
                </h3>
                <p className="text-sm text-secondary mb-4">
                    Choose languages for AI content generation. Each language will generate separate posts.
                </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {SUPPORTED_LANGUAGES.map((language) => {
                    const isSelected = selectedLanguages.includes(language.code);
                    const isLoading = loadingStates.get(language.code) || false;

                    return (
                        <div key={language.code} className="relative">
                            <Checkbox
                                label={
                                    <div className="flex items-center space-x-2">
                                        <span className="text-lg">{language.flag}</span>
                                        <span className="text-sm font-medium">{language.name}</span>
                                    </div>
                                }
                                checked={isSelected}
                                onChange={(e) => handleLanguageToggle(language.code, e.target.checked)}
                                disabled={isLoading}
                                className="w-full"
                            />

                            {isLoading && (
                                <div className="absolute top-1 right-1">
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {selectedLanguages.length > 0 && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                        <strong>{selectedLanguages.length}</strong> language{selectedLanguages.length > 1 ? 's' : ''} selected.
                        AI will generate content in: {selectedLanguages.map(lang =>
                            SUPPORTED_LANGUAGES.find(l => l.code === lang)?.name
                        ).join(', ')}
                    </p>
                </div>
            )}
        </div>
    );
}
