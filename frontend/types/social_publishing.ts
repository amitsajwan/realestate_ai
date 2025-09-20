/**
 * Social Publishing Types
 * ======================
 * TypeScript types for social media publishing workflow
 */

export type Channel = 'facebook' | 'instagram' | 'website';
export type DraftStatus = 'draft' | 'generated' | 'edited' | 'ready' | 'publishing' | 'published' | 'failed';

export interface AIDraft {
    id?: string;
    propertyId: string;
    language: string;       // e.g. 'en-IN', 'mr-IN'
    channel: Channel;
    title: string;
    body: string;
    hashtags: string[];
    mediaIds: string[];
    contactIncluded: boolean;
    status: DraftStatus;
    editedBy?: string;
    updatedAt?: string;
    createdAt?: string;
}

export interface SocialAccount {
    id?: string;
    agentId: string;
    platform: Channel;
    pageId?: string;
    isActive: boolean;
    createdAt?: string;
    updatedAt?: string;
}

export interface SocialPost {
    id?: string;
    draftId: string;
    platformPostId?: string;
    platform: Channel;
    status: 'published' | 'failed' | 'scheduled';
    errorMessage?: string;
    publishedAt?: string;
    createdAt?: string;
}

export interface GenerateContentRequest {
    propertyId: string;
    language: string;
    channels: Channel[];
    tone?: string;
    length?: string;
    agentId: string;
}

export interface GenerateContentResponse {
    drafts: AIDraft[];
}

export interface UpdateDraftRequest {
    title?: string;
    body?: string;
    hashtags?: string[];
    contactIncluded?: boolean;
    mediaIds?: string[];
    status?: DraftStatus;
}

export interface MarkReadyRequest {
    draftIds: string[];
}

export interface PublishRequest {
    draftIds: string[];
    scheduleAt?: string;
}

export interface PublishResponse {
    jobId: string;
    message: string;
}

export interface DraftsResponse {
    propertyId: string;
    language: string;
    drafts: AIDraft[];
}

export interface ContactInfo {
    name: string;
    phone: string;
    whatsapp?: string;
    email?: string;
    website?: string;
}

export interface PropertyContext {
    id: string;
    title: string;
    description: string;
    price: number;
    location: string;
    propertyType: string;
    bedrooms: number;
    bathrooms: number;
    areaSqft: number;
    amenities: string[];
    features: string[];
    images: string[];
}

export interface AIGenerationContext {
    property: PropertyContext;
    agent: ContactInfo;
    language: string;
    channel: Channel;
    tone: string;
    length: string;
}

// UI State Types
export interface PublishingUIState {
    selectedProperty: PropertyContext | null;
    selectedLanguages: string[];
    selectedChannels: Channel[];
    drafts: Map<string, Map<Channel, AIDraft>>; // language -> channel -> draft
    loadingStates: Map<string, boolean>; // language -> loading
    currentLanguage: string;
    currentChannel: Channel;
}

export interface CharLimits {
    maxChars: number;
    maxHashtags: number;
    warningThreshold: number;
}

export interface ToneOptions {
    friendly: string;
    luxury: string;
    investor: string;
}

export interface LengthOptions {
    short: string;
    medium: string;
    long: string;
}

// Component Props
export interface LanguageSelectorProps {
    selectedLanguages: string[];
    onLanguageChange: (languages: string[]) => void;
    onLanguageAdded: (language: string) => void;
    loadingStates: Map<string, boolean>;
}

export interface ChannelSelectorProps {
    selectedChannels: Channel[];
    onChannelChange: (channels: Channel[]) => void;
}

export interface AIContentPanelProps {
    property: PropertyContext;
    language: string;
    channel: Channel;
    draft: AIDraft | null;
    onDraftUpdate: (draft: AIDraft) => void;
    onRegenerate: () => void;
    onImprove: (type: string) => void;
    onMarkReady: () => void;
    isLoading: boolean;
}

export interface ContentEditorProps {
    draft: AIDraft;
    onUpdate: (updates: Partial<AIDraft>) => void;
    limits: CharLimits;
}

export interface PreviewPanelProps {
    draft: AIDraft;
    channel: Channel;
}

export interface PublishBarProps {
    readyDrafts: AIDraft[];
    onPublish: () => void;
    onSchedule: (scheduleAt: string) => void;
    onExport: () => void;
    isPublishing: boolean;
}
