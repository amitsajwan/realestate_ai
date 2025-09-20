'use client'

import { Button, Input, Textarea } from '@/components/UI';
import { ContentEditorProps } from '@/types/social_publishing';
import {
    AdjustmentsHorizontalIcon,
    ArrowPathIcon,
    ArrowsPointingOutIcon,
    FaceSmileIcon,
    MapPinIcon,
    ScissorsIcon
} from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';

export default function ContentEditor({
    draft,
    onUpdate,
    limits
}: ContentEditorProps) {
    const [title, setTitle] = useState(draft.title);
    const [body, setBody] = useState(draft.body);
    const [hashtags, setHashtags] = useState(draft.hashtags.join(' '));
    const [contactIncluded, setContactIncluded] = useState(draft.contactIncluded);

    useEffect(() => {
        setTitle(draft.title);
        setBody(draft.body);
        setHashtags(draft.hashtags.join(' '));
        setContactIncluded(draft.contactIncluded);
    }, [draft]);

    const handleTitleChange = (value: string) => {
        setTitle(value);
        onUpdate({ title: value, status: 'edited' });
    };

    const handleBodyChange = (value: string) => {
        setBody(value);
        onUpdate({ body: value, status: 'edited' });
    };

    const handleHashtagsChange = (value: string) => {
        const hashtagArray = value.split(' ').filter(tag => tag.trim());
        setHashtags(value);
        onUpdate({ hashtags: hashtagArray, status: 'edited' });
    };

    const handleContactToggle = (included: boolean) => {
        setContactIncluded(included);
        onUpdate({ contactIncluded: included, status: 'edited' });
    };

    const getCharCount = () => {
        const totalChars = title.length + body.length + hashtags.length;
        return totalChars;
    };

    const getCharStatus = () => {
        const count = getCharCount();
        const percentage = (count / limits.maxChars) * 100;

        if (percentage >= 100) return { color: 'text-red-500', bg: 'bg-red-100' };
        if (percentage >= limits.warningThreshold) return { color: 'text-yellow-500', bg: 'bg-yellow-100' };
        return { color: 'text-green-500', bg: 'bg-green-100' };
    };

    const getHashtagCount = () => {
        return hashtags.split(' ').filter(tag => tag.trim()).length;
    };

    const charStatus = getCharStatus();
    const charCount = getCharCount();
    const hashtagCount = getHashtagCount();

    return (
        <div className="space-y-6">
            {/* Title Input */}
            <div>
                <Input
                    label="Post Title"
                    value={title}
                    onChange={(e) => handleTitleChange(e.target.value)}
                    placeholder="Enter compelling headline..."
                />
                <p className="mt-1 text-sm text-gray-500">{title.length}/100 characters</p>
            </div>

            {/* Body Textarea */}
            <div>
                <Textarea
                    label="Post Content"
                    value={body}
                    onChange={(e) => handleBodyChange(e.target.value)}
                    placeholder="Write your post content here..."
                    rows={6}
                />
                <div className="mt-2 flex justify-between items-center text-sm">
                    <span className="text-secondary">
                        {body.length} characters
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${charStatus.bg} ${charStatus.color}`}>
                        {charCount}/{limits.maxChars} total
                    </span>
                </div>
            </div>

            {/* Hashtags Input */}
            <div>
                <Input
                    label="Hashtags"
                    value={hashtags}
                    onChange={(e) => handleHashtagsChange(e.target.value)}
                    placeholder="#realestate #property #investment #home"
                />
                <p className="mt-1 text-sm text-gray-500">{hashtagCount}/{limits.maxHashtags} hashtags</p>
            </div>

            {/* Contact Information Toggle */}
            <div className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                <div className="flex items-center justify-between">
                    <div>
                        <h4 className="font-medium text-primary">Include Agent Contact</h4>
                        <p className="text-sm text-secondary">
                            Add your contact information to the post
                        </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            checked={contactIncluded}
                            onChange={(e) => handleContactToggle(e.target.checked)}
                            className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>
            </div>

            {/* Improvement Tools */}
            <div className="space-y-4">
                <h4 className="font-medium text-primary">Improve Content</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement regenerate */ }}
                        className="flex items-center space-x-2"
                    >
                        <ArrowPathIcon className="w-4 h-4" />
                        <span>Regenerate</span>
                    </Button>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement tone improvement */ }}
                        className="flex items-center space-x-2"
                    >
                        <AdjustmentsHorizontalIcon className="w-4 h-4" />
                        <span>Improve Tone</span>
                    </Button>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement shorter */ }}
                        className="flex items-center space-x-2"
                    >
                        <ScissorsIcon className="w-4 h-4" />
                        <span>Shorter</span>
                    </Button>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement longer */ }}
                        className="flex items-center space-x-2"
                    >
                        <ArrowsPointingOutIcon className="w-4 h-4" />
                        <span>Longer</span>
                    </Button>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement emojis */ }}
                        className="flex items-center space-x-2"
                    >
                        <FaceSmileIcon className="w-4 h-4" />
                        <span>Add Emojis</span>
                    </Button>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Implement facts */ }}
                        className="flex items-center space-x-2"
                    >
                        <MapPinIcon className="w-4 h-4" />
                        <span>Add Facts</span>
                    </Button>
                </div>
            </div>

            {/* Character Limits Warning */}
            {charCount > limits.maxChars && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-300">
                        ⚠️ Content exceeds character limit by {charCount - limits.maxChars} characters.
                        Please shorten the content.
                    </p>
                </div>
            )}

            {hashtagCount > limits.maxHashtags && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-300">
                        ⚠️ Too many hashtags ({hashtagCount}/{limits.maxHashtags}).
                        Please remove some hashtags.
                    </p>
                </div>
            )}
        </div>
    );
}
