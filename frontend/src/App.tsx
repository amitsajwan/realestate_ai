import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { marked } from 'marked';
import Onboarding from './components/Onboarding';

// --- Helper: Generate Listing Post ---
function generateListingPost() {
  console.log("Generate listing post")
  const token = localStorage.getItem('jwt_token');
  const rawPrice = '₹1,00,00,000';
  const rawFeatures = 'Sea view, Gym, Pool';
  const payload = {
    template: 'just_listed',
    address: '123 Main St',
    city: 'Pune',
    state: 'MH',
    price: String(rawPrice),
    bedrooms: 3,
    bathrooms: 2.0,
    features: rawFeatures.split(',').map(f => f.trim()).filter(f => f.length > 0),
  };
  fetch('/api/listings/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify(payload)
  })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) {
        alert('Error: ' + (data.detail || JSON.stringify(data)));
      } else {
        alert('Listing Post Generated: ' + JSON.stringify(data));
      }
    })
    .catch(err => {
      alert('Error generating listing post: ' + err);
    });
}

// --- UI Components ---

const Spinner = () => (
  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
);

type ChatBubbleProps = { message: string; from: 'user' | 'assistant' };
const ChatBubble = ({ message, from }: ChatBubbleProps) => (
  <div className={`flex w-full ${from === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
    <div
      className={`rounded-lg px-4 py-2 max-w-lg shadow-md ${
        from === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
      }`}
      dangerouslySetInnerHTML={{ __html: marked.parse(message || '') as string }}
    ></div>
  </div>
);

type StageDisplayProps = { title: string; data?: string; isLoading?: boolean };
const StageDisplay = ({ title, data, isLoading }: StageDisplayProps) => {
  if (!data && !isLoading) return null;
  return (
    <div className="bg-white p-4 rounded-lg shadow-lg mb-4 border border-gray-200 animate-fade-in">
      <h3 className="font-bold text-lg mb-2 text-gray-800">{title}</h3>
      {isLoading && !data && <div className="text-gray-500 italic">Generating...</div>}
      {data && (
        <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: marked.parse(data) as string }} />
      )}
    </div>
  );
};

type ImageDisplayProps = { title: string; imageUrl?: string | null; isLoading?: boolean };
const ImageDisplay = ({ title, imageUrl, isLoading }: ImageDisplayProps) => {
  if (!imageUrl && !isLoading) return null;
  return (
    <div className="bg-white p-4 rounded-lg shadow-lg mb-4 border border-gray-200 animate-fade-in">
      <h3 className="font-bold text-lg mb-2 text-gray-800">{title}</h3>
      <div className="w-full aspect-square bg-gray-100 rounded-md flex items-center justify-center overflow-hidden">
        {isLoading && <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>}
        {imageUrl && (
          <img
            src={`http://localhost:8000${imageUrl}?t=${new Date().getTime()}`}
            alt="Generated property visual"
            className="rounded-md object-cover w-full h-full"
          />
        )}
      </div>
    </div>
  );
};

type Details = { location: string; price: string; bedrooms: string; features: string; should_post?: boolean };
type DetailsFormProps = { onSubmit: (details: Details) => void; isLoading?: boolean };
const DetailsForm = ({ onSubmit, isLoading }: DetailsFormProps) => {
  const [details, setDetails] = useState<Details>({ location: '', price: '', bedrooms: '', features: '', should_post: false });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDetails({ ...details, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(details);
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-xl mb-4 border-2 border-indigo-500 animate-fade-in">
      <h3 className="font-bold text-lg mb-3 text-indigo-600">Action Required: Provide Property Details</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input name="location" value={details.location} onChange={handleChange} placeholder="Location (e.g., Kharadi, Pune)" className="w-full p-2 border rounded-md focus:ring-2 focus:ring-indigo-400" required />
        <input name="price" value={details.price} onChange={handleChange} placeholder="Price (e.g., 1.5 Cr)" className="w-full p-2 border rounded-md focus:ring-2 focus:ring-indigo-400" required />
        <input name="bedrooms" value={details.bedrooms} onChange={handleChange} placeholder="Bedrooms (e.g., 2 BHK)" className="w-full p-2 border rounded-md focus:ring-2 focus:ring-indigo-400" required />
        <input name="features" value={details.features} onChange={handleChange} placeholder="Key Features (comma-separated)" className="w-full p-2 border rounded-md focus:ring-2 focus:ring-indigo-400" required />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={!!details.should_post}
            onChange={(e) => setDetails(prev => ({ ...prev, should_post: e.target.checked }))}
          />
          Post to Facebook
        </label>
        <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded-md hover:bg-indigo-700 font-semibold flex items-center justify-center" disabled={isLoading}>
          {isLoading ? <Spinner /> : (details.should_post ? 'Generate & Post' : 'Generate (Preview Only)')}
        </button>
      </form>
    </div>
  );
};

// --- Main App Component ---

type Msg = { from: 'user' | 'assistant'; text: string };
type WorkflowState = {
  brand_suggestions?: string;
  image_path?: string | null;
  base_post?: string;
  post_result?: { message?: string };
  [key: string]: any;
};

const App = () => {
  const [clientId] = useState<string>(uuidv4());
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showDetailsForm, setShowDetailsForm] = useState(false);
  const [workflowState, setWorkflowState] = useState<WorkflowState>({});
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});

  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsBase = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
      ? `ws://localhost:3000`
      : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`;
    ws.current = new WebSocket(`${wsBase}/chat/${clientId}`);

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setMessages([{ from: 'assistant', text: 'Hi! What\'s the core idea for your new project or brand? For example, "luxury villas in Goa".' }]);
    };
    
    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
      setMessages(prev => [...prev, { 
        from: 'assistant', 
        text: 'Connection lost. Trying to reconnect...' 
      }]);
      
      // Attempt to reconnect after 3 seconds with smart URL detection
      setTimeout(() => {
        if (ws.current?.readyState === WebSocket.CLOSED) {
          const retryBase = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
            ? `ws://localhost:8003`  // Use our main backend port
            : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`;
          ws.current = new WebSocket(`${retryBase}/chat/${clientId}`);
        }
      }, 3000);
    };

    ws.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("Received WS Message:", msg);

        switch (msg.type) {
          case 'update':
            setLoadingStates((prev: Record<string, boolean>) => ({ ...prev, [msg.step as string]: false }));
            setWorkflowState((prev: WorkflowState) => ({ ...prev, ...(msg.data as Record<string, any>) }));
            break;
          case 'request_input':
            setShowDetailsForm(true);
            setMessages(prev => [...prev, { from: 'assistant', text: 'Branding complete! Now I need a few more details to create the post. Please fill out the form on the right.' }]);
            break;
          case 'error':
            setMessages(prev => [...prev, { from: 'assistant', text: `**Error:** ${msg.message}` }]);
            setLoadingStates({});
            break;
          case 'final':
            setMessages(prev => [...prev, { from: 'assistant', text: msg.message || '✅ All done!' }]);
            setLoadingStates((prev: Record<string, boolean>) => ({ ...prev, post_to_facebook: false }));
            break;
          default:
            console.warn("Unhandled WebSocket message type:", msg.type);
            break;
        }
      } catch (e) {
        console.error("Invalid JSON received:", event.data, e);
      }
    };

    ws.current.onclose = () => console.log('WebSocket Disconnected');
    ws.current.onerror = (error) => console.error('WebSocket Error:', error);

    return () => {
      if(ws.current) ws.current.close();
    };
  }, [clientId]);

  const handleSendInitialInput = () => {
    if (input.trim() === '') return;
    setWorkflowState({});
    setShowDetailsForm(false);
    setMessages(prev => [...prev, { from: 'user', text: input }]);
    // Check WebSocket connection state before sending
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "initial_input", user_input: input }));
      setInput('');
      setLoadingStates({ create_branding: true, create_visuals: true, generate_image: true });
    } else {
      setMessages(prev => [...prev, { 
        from: 'assistant', 
        text: 'Connection not ready. Please wait and try again.' 
      }]);
    }
  };

  const handleDetailsSubmit = (details: Details) => {
    const payload = {
      address: details.location,
      price: details.price,
      property_type: 'apartment',
      bedrooms: details.bedrooms,
      bathrooms: '',
      features: details.features,
      template: 'just_listed',
      language: 'en',
      auto_generate: true
    };
    setShowDetailsForm(false);
    setMessages(prev => [...prev, { from: 'user', text: `Here are the property details.` }]);
    setLoadingStates((prev: Record<string, boolean>) => ({ ...prev, generate_post: true, post_to_facebook: !!details.should_post }));

    const token = localStorage.getItem('jwt_token');
    fetch('/api/smart-properties', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        setMessages(prev => [...prev, { from: 'assistant', text: `Smart Property Created: ${JSON.stringify(data)}` }]);
        setLoadingStates((prev: Record<string, boolean>) => ({ ...prev, generate_post: false }));
      })
      .catch(err => {
        setMessages(prev => [...prev, { from: 'assistant', text: `Error creating Smart Property: ${err}` }]);
        setLoadingStates((prev: Record<string, boolean>) => ({ ...prev, generate_post: false }));
      });
  };

  return (
    <div className="flex h-screen font-sans bg-gray-100">
      {/* Left Panel: Chat */}
      <div className="w-1/2 bg-white flex flex-col p-4 border-r">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">AI Assistant</h2>
        <div className="flex-grow overflow-y-auto pr-2 space-y-4">
          {messages.map((msg, i) => <ChatBubble key={i} message={msg.text} from={msg.from} />)}
        </div>
        <div className="mt-4 flex border-t pt-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendInitialInput()}
            className="flex-grow p-3 border rounded-l-md focus:ring-2 focus:ring-indigo-500"
            placeholder="Type your business idea..."
            disabled={Object.keys(workflowState).length > 0}
          />
          <button onClick={handleSendInitialInput} className="bg-indigo-600 text-white px-6 py-3 rounded-r-md font-semibold" disabled={Object.keys(workflowState).length > 0}>
            Start
          </button>
        </div>
        <button
          className="mt-4 bg-green-600 text-white px-4 py-2 rounded font-semibold"
          onClick={generateListingPost}
        >
          Generate Listing Post (Test)
        </button>
      </div>

      {/* Right Panel: Workflow Status & Form */}
      <div className="w-1/2 p-6 overflow-y-auto bg-gray-50">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Workflow Status</h2>
        {Object.keys(workflowState).length === 0 && Object.keys(loadingStates).length === 0 && (
          <div className="text-center text-gray-500 mt-16 p-8 bg-white rounded-lg shadow-inner">
            <p>Your generated content will appear here step-by-step.</p>
          </div>
        )}
        <StageDisplay title="1. Branding Suggestions" data={workflowState.brand_suggestions} isLoading={loadingStates.create_branding} />
        <ImageDisplay title="2. Visual Concept" imageUrl={workflowState.image_path} isLoading={loadingStates.generate_image} />
        {showDetailsForm && <DetailsForm onSubmit={handleDetailsSubmit} isLoading={loadingStates.generate_post} />}
        <StageDisplay title="3. Final Post Content" data={workflowState.base_post} isLoading={loadingStates.generate_post} />
        <StageDisplay title="4. Publishing Status" data={workflowState.post_result?.message} isLoading={loadingStates.post_to_facebook} />
        <div className="mt-8">
          <Onboarding />
        </div>
      </div>
    </div>
  );
};

export default App;