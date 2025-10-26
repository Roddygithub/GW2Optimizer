import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X, Bot, ChevronDown, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { cn } from '../../utils/cn';
import { chatAPI } from '../../services/api';
import ChatMessage, { Message } from './ChatMessage';
import { useAppVersion } from '../../hooks/useAppVersion';

export type { Message };

const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = 'Textarea';
export interface ChatBoxProps {
  defaultOpen?: boolean;
  className?: string;
}

export const ChatBox = ({ defaultOpen = true, className }: ChatBoxProps) => {
  const getIsDesktop = () => (typeof window !== 'undefined' ? window.innerWidth >= 1024 : true);
  const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      content: 'Bonjour ! Je suis l\'assistant GW2 Optimizer. Comment puis-je vous aider aujourd\'hui ?',
      role: 'assistant',
      timestamp: new Date(),
      suggestions: [
        'Crée-moi une composition pour un raid',
        'Quel est le meilleur build pour un Gardien ?',
        'Comment optimiser mon DPS en tant qu\'Élémentariste ?'
      ],
      // Assurer que les builds sont correctement typés
      builds: []
    },
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { version } = useAppVersion();

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current?.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Auto-focus on input when chat is opened
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  // Responsive handling is CSS-driven; no need for window resize listeners here

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      content: input,
      role: 'user',
      timestamp: new Date(),
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(input, version);
      
      const assistantMessage: Message = {
        id: generateId(),
        content: response.response || 'Je n\'ai pas pu traiter votre demande.',
        role: 'assistant',
        timestamp: new Date(),
        builds: response.builds_mentioned,
        suggestions: response.suggestions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: 'Une erreur est survenue. Veuillez réessayer plus tard.',
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // Timestamp formatting, build/suggestion guards are handled in ChatMessage component

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    // Focus on the input after setting the suggestion
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  };

  return (
    <div className={cn('fixed z-50', className)}>
      {/* Mobile: Bottom dock */}
      <div className="lg:hidden fixed bottom-6 right-6 z-50">
        <AnimatePresence>
          {isOpen ? (
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              className="fixed inset-0 bg-background/95 backdrop-blur-sm lg:hidden"
              onClick={() => setIsOpen(false)}
            />
          ) : null}
        </AnimatePresence>

        <AnimatePresence>
          {isOpen ? (
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25 }}
              className="fixed bottom-0 left-0 right-0 bg-background border-t border-border rounded-t-2xl shadow-2xl flex flex-col"
              style={{ height: '80vh' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-gw2-gold" />
                  <h3 className="font-semibold">Assistant GW2 Optimizer</h3>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleChat}
                  className="h-8 w-8"
                  aria-label="Fermer le chat"
                >
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-muted-foreground">
                    <Bot className="h-12 w-12 text-gw2-gold mb-4" />
                    <h3 className="text-lg font-medium mb-2">Comment puis-je vous aider ?</h3>
                    <p className="text-sm max-w-xs">
                      Posez-moi des questions sur les builds, les compositions d'équipe ou les stratégies WvW.
                    </p>
                  </div>
                ) : (
                  <>
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        message={message}
                        onSuggestionClick={handleSuggestionClick}
                      />
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              <form onSubmit={handleSubmit} className="p-4 border-t border-border">
                <div className="relative">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Posez votre question..."
                    className="pr-12 resize-none"
                    rows={1}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                  />
                  <Button
                    type="submit"
                    size="icon"
                    disabled={!input.trim() || isLoading}
                    className="absolute right-2 bottom-2 h-8 w-8"
                    aria-label="Envoyer le message"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  GW2 Optimizer v{version} - L'IA peut faire des erreurs. Vérifiez les informations importantes.
                </p>
              </form>
            </motion.div>
          ) : (
            <motion.div
              initial={{ y: 0, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              className="flex justify-end"
            >
              <Button
                onClick={toggleChat}
                className="rounded-full h-14 w-14 p-0 bg-gw2-gold hover:bg-gw2-gold/90 text-white shadow-lg shadow-gw2-gold/30"
                aria-label={isOpen ? 'Fermer le chat' : 'Ouvrir le chat'}
              >
                <Bot className="h-6 w-6" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Desktop: Side dock */}
      <div className="hidden lg:block fixed right-6 bottom-6 z-50">
        <AnimatePresence>
          {isOpen ? (
            <motion.div
              initial={{ x: 300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 300, opacity: 0 }}
              transition={{ type: 'spring', damping: 25 }}
              className="w-96 bg-background rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col"
              style={{ height: 'calc(100vh - 120px)', maxHeight: '800px' }}
            >
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-gw2-gold" />
                  <h3 className="font-semibold">Assistant GW2 Optimizer</h3>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleChat}
                  className="h-8 w-8"
                  aria-label="Fermer le chat"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-muted-foreground">
                    <Bot className="h-16 w-16 text-gw2-gold/50 mb-4" />
                    <h3 className="text-xl font-medium mb-2">Comment puis-je vous aider ?</h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      Je peux vous aider avec les builds, les compositions d'équipe et les stratégies WvW.
                      Essayez de me demander :
                    </p>
                    <div className="grid gap-2 w-full max-w-xs">
                      <button
                        type="button"
                        onClick={() => setInput("Quels sont les meilleurs builds pour gardien en WvW ?")}
                        className="text-sm p-3 rounded-lg border border-border hover:bg-accent/50 text-left transition-colors"
                      >
                        "Quels sont les meilleurs builds pour gardien en WvW ?"
                      </button>
                      <button
                        type="button"
                        onClick={() => setInput("Comment composer une escouade équilibrée ?")}
                        className="text-sm p-3 rounded-lg border border-border hover:bg-accent/50 text-left transition-colors"
                      >
                        "Comment composer une escouade équilibrée ?"
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        message={message}
                        onSuggestionClick={handleSuggestionClick}
                        className={message.role === 'user' ? 'ml-auto' : 'mr-auto'}
                      />
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              <form onSubmit={handleSubmit} className="p-4 border-t border-border">
                <div className="relative">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Posez votre question sur GW2 WvW..."
                    className="pr-12 resize-none"
                    rows={3}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                  />
                  <Button
                    type="submit"
                    size="icon"
                    disabled={!input.trim() || isLoading}
                    className="absolute right-2 bottom-2 h-8 w-8"
                    aria-label="Envoyer le message"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  GW2 Optimizer v{version} - L'IA peut faire des erreurs. Vérifiez les informations importantes.
                </p>
              </form>
            </motion.div>
          ) : (
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex justify-end"
            >
              <Button
                onClick={toggleChat}
                className="rounded-full h-16 w-16 p-0 bg-gw2-gold hover:bg-gw2-gold/90 text-white shadow-lg shadow-gw2-gold/30"
                aria-label={isOpen ? 'Fermer le chat' : 'Ouvrir le chat'}
              >
                <Bot className="h-7 w-7" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ChatBox;
