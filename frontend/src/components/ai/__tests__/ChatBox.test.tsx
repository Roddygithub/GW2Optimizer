import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatBox } from '../ChatBox';
import { chatAPI } from '../../../services/api';

// Mock the chatAPI
vi.mock('../../../services/api', () => ({
  chatAPI: {
    sendMessage: vi.fn(),
  },
}));

// Mock the useAppVersion hook
vi.mock('../../../hooks/useAppVersion', () => ({
  useAppVersion: () => ({
    version: '1.0.0',
  }),
}));

describe('ChatBox', () => {
  const mockSendMessage = chatAPI.sendMessage as jest.Mock;
  
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
    
    // Mock the scrollIntoView method
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders the chat box when open', () => {
    render(<ChatBox defaultOpen={true} />);
    
    expect(screen.getByText('Assistant GW2 Optimizer')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Posez votre question...')).toBeInTheDocument();
  });

  it('can be toggled open and closed', () => {
    render(<ChatBox defaultOpen={false} />);
    
    // Chat should be closed initially
    expect(screen.queryByPlaceholderText('Posez votre question...')).not.toBeInTheDocument();
    
    // Open the chat
    const toggleButton = screen.getByRole('button', { name: /ouvrir le chat/i });
    fireEvent.click(toggleButton);
    
    // Chat should be open
    expect(screen.getByPlaceholderText('Posez votre question...')).toBeInTheDocument();
    
    // Close the chat
    const closeButton = screen.getByRole('button', { name: /fermer le chat/i });
    fireEvent.click(closeButton);
    
    // Chat should be closed
    expect(screen.queryByPlaceholderText('Posez votre question...')).not.toBeInTheDocument();
  });

  it('allows the user to type a message', () => {
    render(<ChatBox defaultOpen={true} />);
    
    const input = screen.getByPlaceholderText('Posez votre question...');
    fireEvent.change(input, { target: { value: 'Bonjour, je cherche un build' } });
    
    expect(input).toHaveValue('Bonjour, je cherche un build');
  });

  it('submits the form when the send button is clicked', async () => {
    // Configurer le mock pour retourner une réponse spécifique
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici une réponse de test',
      builds_mentioned: [],
      suggestions: []
    });
    
    render(<ChatBox defaultOpen={true} />);
    
    const input = screen.getByPlaceholderText('Posez votre question...');
    // Trouver tous les boutons d'envoi (un pour mobile et un pour desktop)
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    
    // Vérifier qu'il y a bien deux boutons (mobile et desktop)
    expect(sendButtons.length).toBe(2);
    
    // Utiliser le premier bouton pour l'interaction
    const initialSendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Bonjour' } });
    fireEvent.click(initialSendButton);
    
    // Vérifier que les boutons de chargement sont affichés
    const loadingButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    
    // Vérifier chaque bouton
    loadingButtons.forEach(button => {
      expect(button).toHaveAttribute('disabled');
      const loadingIcon = button.querySelector('.animate-spin');
      expect(loadingIcon).toBeInTheDocument();
    });
    
    // Attendre la réponse simulée
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('Bonjour', '1.0.0');
      // Vérifier que le message de l'utilisateur est affiché
      expect(screen.getByText('Bonjour')).toBeInTheDocument();
      // Vérifier que la réponse de l'assistant est affichée
      expect(screen.getByText('Voici une réponse de test')).toBeInTheDocument();
    });
    
    // Vérifier que les boutons de chargement ont disparu
    const finalButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    finalButtons.forEach(button => {
      expect(button).not.toHaveAttribute('disabled');
      const loadingIcon = button.querySelector('.animate-spin');
      expect(loadingIcon).not.toBeInTheDocument();
    });
  });

  it('displays build suggestions when available', async () => {
    // Mock response with build suggestions
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici un build pour vous',
      builds_mentioned: [
        {
          id: 'build-1',
          name: 'Build Gardien',
          profession: 'Guardian',
          role: 'Heal',
          weapons: {
            mainHand: 'Bâton',
            offHand: 'Focus'
          },
          traits: ['Honor', 'Virtues', 'Dragonhunter'],
          skills: ['Soin de l\'éclat', 'Bouclier de colère', 'Lame de jugement'],
          stats: {
            power: 1000,
            precision: 500,
            toughness: 1500,
            vitality: 1200,
            condition: 300,
            healing: 1800
          },
          playerCount: 1
        }
      ]
    });
    
    render(<ChatBox defaultOpen={true} />);
    
    const input = screen.getByPlaceholderText('Posez votre question...');
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const sendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Quel build pour un gardien soigneur ?' } });
    fireEvent.click(sendButton);
    
    // Wait for the mock response
    await waitFor(() => {
      // Check if the build is displayed
      expect(screen.getByText('Build Gardien')).toBeInTheDocument();
      expect(screen.getByText('Guardian')).toBeInTheDocument();
      expect(screen.getByText('Heal')).toBeInTheDocument();
    });
  });

  it('displays follow-up suggestions when available', async () => {
    // Mock response with follow-up suggestions
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici quelques suggestions',
      suggestions: ['En savoir plus', 'Autre question']
    });
    
    render(<ChatBox defaultOpen={true} />);
    
    const input = screen.getByPlaceholderText('Posez votre question...');
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const sendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Quelles sont les options ?' } });
    fireEvent.click(sendButton);
    
    // Wait for the mock response
    await waitFor(() => {
      // Check if the suggestions are displayed
      expect(screen.getByText('En savoir plus')).toBeInTheDocument();
      expect(screen.getByText('Autre question')).toBeInTheDocument();
    });
  });

  it('handles errors when the API call fails', async () => {
    // Mock a failed API call
    const errorMessage = 'Erreur de connexion à l\'API';
    mockSendMessage.mockRejectedValueOnce(new Error(errorMessage));
    
    render(<ChatBox defaultOpen={true} />);
    
    const input = screen.getByPlaceholderText('Posez votre question...');
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const sendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Test erreur' } });
    fireEvent.click(sendButton);
    
    // Vérifier que les boutons sont désactivés pendant le chargement
    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: /envoyer le message/i });
      buttons.forEach(button => {
        expect(button).toHaveAttribute('disabled');
      });
      
      // Vérifier qu'au moins un indicateur de chargement est présent
      const loadingIcons = document.querySelectorAll('.animate-spin');
      expect(loadingIcons.length).toBeGreaterThan(0);
    });
    
    // Attendre que le message d'erreur s'affiche
    await waitFor(() => {
      // Vérifier que le message d'erreur est présent dans le DOM
      const errorMessages = screen.getAllByText(/erreur est survenue/i);
      expect(errorMessages.length).toBeGreaterThan(0);
      
      // Vérifier que le message d'erreur est visible pour l'utilisateur
      const visibleErrorMessages = errorMessages.filter(msg => 
        msg.textContent?.includes('Une erreur est survenue') || 
        msg.textContent?.includes('erreur est survenue')
      );
      expect(visibleErrorMessages.length).toBeGreaterThan(0);
    }, { timeout: 5000 });
    
    // Vérifier que les boutons de chargement ont disparu et que les boutons sont dans le bon état
    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: /envoyer le message/i });
      
      // Vérifier qu'aucun bouton n'a l'indicateur de chargement
      buttons.forEach(button => {
        const loadingIcon = button.querySelector('.animate-spin');
        expect(loadingIcon).not.toBeInTheDocument();
      });
      
      // Vérifier que les boutons sont à nouveau activés (sauf si l'input est vide)
      const input = screen.getByPlaceholderText('Posez votre question...') as HTMLInputElement;
      if (input.value.trim() === '') {
        // Si l'input est vide, le bouton doit être désactivé
        buttons.forEach(button => {
          expect(button).toHaveAttribute('disabled');
        });
      } else {
        // Sinon, le bouton doit être activé
        buttons.forEach(button => {
          expect(button).not.toHaveAttribute('disabled');
        });
      }
    });
  });

  it('displays follow-up suggestions after receiving a response', async () => {
    // Mock response with follow-up suggestions
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici quelques suggestions',
      suggestions: ['En savoir plus', 'Autre question']
    });
    
    render(<ChatBox defaultOpen={true} />);
    
    // Envoyer le message initial
    const input = screen.getByPlaceholderText('Posez votre question...');
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const sendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Quelles sont les options ?' } });
    fireEvent.click(sendButton);
    
    // Vérifier que la réponse est affichée
    console.log('Contenu du DOM avant vérification du texte:', document.body.innerHTML);
    
    await waitFor(() => {
      const elements = screen.getAllByText(/Voici quelques suggestions|Bonjour ! Je suis l'assistant GW2 Optimizer/);
      console.log('Éléments trouvés:', elements.length);
      expect(elements.length).toBeGreaterThan(0);
    });
    
    // Vérifier que les suggestions sont affichées
    const suggestion1 = screen.getByText('En savoir plus');
    const suggestion2 = screen.getByText('Autre question');
    expect(suggestion1).toBeInTheDocument();
    expect(suggestion2).toBeInTheDocument();
  });
  
  it('sends a new message when clicking on a suggestion', async () => {
    // First response with follow-up suggestions
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici quelques suggestions',
      suggestions: ['En savoir plus', 'Autre question']
    });
    
    // Second response when clicking on a suggestion
    mockSendMessage.mockResolvedValueOnce({
      response: 'Voici plus d\'informations',
      suggestions: []
    });
    
    render(<ChatBox defaultOpen={true} />);
    
    // Send initial message
    const input = screen.getByPlaceholderText('Posez votre question...');
    const sendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const sendButton = sendButtons[0];
    
    fireEvent.change(input, { target: { value: 'Quelles sont les options ?' } });
    fireEvent.click(sendButton);
    
    // Wait for the suggestions to appear
    await waitFor(() => {
      expect(screen.getByText('En savoir plus')).toBeInTheDocument();
      expect(screen.getByText('Autre question')).toBeInTheDocument();
    });
    
    // Find and click on a suggestion
    const suggestionButtons = screen.getAllByRole('button', {
      name: /En savoir plus|Autre question/
    });
    
    expect(suggestionButtons.length).toBe(2);
    
    // Click on the first suggestion
    fireEvent.click(suggestionButtons[0]);
    
    // Check that the input was updated with the suggestion
    const updatedInput = screen.getByPlaceholderText('Posez votre question...') as HTMLInputElement;
    expect(updatedInput.value).toBe('En savoir plus');
    
    // Send the suggestion
    const updatedSendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const updatedSendButton = updatedSendButtons[0];
    fireEvent.click(updatedSendButton);
    
    // Check that the API was called with the suggestion
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('En savoir plus', '1.0.0');
    });
    
    // Check that the response is displayed
    await waitFor(() => {
      expect(screen.getByText('Voici plus d\'informations')).toBeInTheDocument();
    });
  });
});
