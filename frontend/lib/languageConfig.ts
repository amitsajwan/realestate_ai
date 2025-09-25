/**
 * Standardized language configuration for AI Content Generation
 * This ensures consistency across all AI components in the application
 */

export interface LanguageOption {
    code: string;
    name: string;
    nativeName?: string;
}

export const STANDARD_LANGUAGES: LanguageOption[] = [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
    { code: 'ur', name: 'Urdu', nativeName: 'اردو' }
];

/**
 * Get language name by code
 */
export const getLanguageName = (code: string): string => {
    const language = STANDARD_LANGUAGES.find(lang => lang.code === code);
    return language?.name || code;
};

/**
 * Get language native name by code
 */
export const getLanguageNativeName = (code: string): string => {
    const language = STANDARD_LANGUAGES.find(lang => lang.code === code);
    return language?.nativeName || language?.name || code;
};

/**
 * Get language display name (shows both English and native name if available)
 */
export const getLanguageDisplayName = (code: string): string => {
    const language = STANDARD_LANGUAGES.find(lang => lang.code === code);
    if (!language) return code;

    if (language.nativeName && language.nativeName !== language.name) {
        return `${language.name} (${language.nativeName})`;
    }

    return language.name;
};
