import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { UploadCloud } from 'lucide-react';

const UploadSection: React.FC = () => {
    const { uploadImage, isLoading } = useAppStore();
    const [file, setFile] = useState<File | null>(null);
    const [notes, setNotes] = useState('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;
        await uploadImage(file, notes);
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-md">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
                <UploadCloud className="mr-2" /> Upload Machine Image
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:bg-gray-50 transition">
                    <input 
                        type="file" 
                        accept="image/*" 
                        onChange={handleFileChange} 
                        className="hidden" 
                        id="image-upload"
                    />
                    <label htmlFor="image-upload" className="cursor-pointer block">
                        {file ? (
                            <span className="text-green-600 font-medium">{file.name}</span>
                        ) : (
                            <span className="text-gray-500">Click to upload or drag and drop</span>
                        )}
                    </label>
                </div>
                
                <textarea
                    placeholder="Describe the issue (optional)..."
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    rows={3}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                />

                <button 
                    type="submit" 
                    disabled={!file || isLoading}
                    className={`w-full py-3 rounded-lg text-white font-semibold transition ${
                        !file || isLoading 
                        ? 'bg-gray-400 cursor-not-allowed' 
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                >
                    {isLoading ? 'Analyzing...' : 'Analyze Machine'}
                </button>
            </form>
        </div>
    );
};

export default UploadSection;
