'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SessionTemplateSearchRequest } from '@/types/api';
import { useTemplateCategories } from '@/hooks/use-session-templates';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (params: SessionTemplateSearchRequest) => void;
  onClear?: () => void;
}

export function SearchBar({ onSearch, onClear }: SearchBarProps) {
  const categories = useTemplateCategories();
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  const handleSearch = () => {
    const params: SessionTemplateSearchRequest = {};

    if (searchTerm.trim()) {
      params.search_term = searchTerm.trim();
    }

    if (category) {
      params.category = category;
    }

    if (tags.length > 0) {
      params.tags = tags;
    }

    onSearch(params);
  };

  const handleClear = () => {
    setSearchTerm('');
    setCategory('');
    setTags([]);
    setTagInput('');
    onClear?.();
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const hasActiveFilters = searchTerm || category || tags.length > 0;

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-lg border">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Search Term */}
        <div className="space-y-2">
          <Label htmlFor="search-term">Search Templates</Label>
          <Input
            id="search-term"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or description..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
        </div>

        {/* Category Filter */}
        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger id="category">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All categories</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat} className="capitalize">
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Tags Filter */}
      <div className="space-y-2">
        <Label>Tags</Label>
        <div className="flex gap-2">
          <Input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            placeholder="Filter by tags..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddTag();
              }
            }}
          />
          <Button type="button" onClick={handleAddTag} variant="outline">
            Add
          </Button>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {tags.map((tag) => (
              <span
                key={tag}
                className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-sm flex items-center gap-1"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 justify-end">
        {hasActiveFilters && (
          <Button type="button" variant="outline" onClick={handleClear}>
            <X className="h-4 w-4 mr-2" />
            Clear
          </Button>
        )}
        <Button type="button" onClick={handleSearch}>
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>
    </div>
  );
}
