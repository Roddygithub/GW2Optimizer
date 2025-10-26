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

const buildTestId = (name: string) => `build-card-${name.toLowerCase().replace(/\s+/g, '-')}`;
const suggestionTestId = (label: string) => `suggestion-${label.toLowerCase().replace(/\s+/g, '-')}`;

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
    
    expect(screen.getAllByText('Assistant GW2 Optimizer').length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText('Posez votre question...')).toBeInTheDocument();
  });

  it('can be toggled open and closed', async () => {
    render(<ChatBox defaultOpen={false} />);
    
    // Chat should be closed initially
    expect(screen.queryByPlaceholderText('Posez votre question...')).not.toBeInTheDocument();
    
    // Open the chat
    const toggleButtons = screen.getAllByRole('button', { name: /ouvrir le chat/i });
    fireEvent.click(toggleButtons[0]);
    
    // Chat should be open
    expect(screen.getByPlaceholderText('Posez votre question...')).toBeInTheDocument();
    
    // Close the chat
    const closeButtons = screen.getAllByRole('button', { name: /fermer le chat/i });
    fireEvent.click(closeButtons[0]);
    
    // Chat should be closed
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Posez votre question...')).not.toBeInTheDocument();
    });
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
    
    // Attendre la réponse simulée et vérifier l'appel API
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('Bonjour', '1.0.0');
    });

    const userMessages = await screen.findAllByText('Bonjour');
    expect(userMessages.length).toBeGreaterThan(0);

    const assistantMessages = await screen.findAllByText('Voici une réponse de test');
    expect(assistantMessages.length).toBeGreaterThan(0);
    
    // Vérifier que les boutons de chargement ont disparu et que les boutons sont désactivés car le champ est vide
    const finalButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    finalButtons.forEach(button => {
      expect(button).toHaveAttribute('disabled');
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
      const buildCards = screen.getAllByTestId(buildTestId('Build Gardien'));
      expect(buildCards.length).toBeGreaterThan(0);
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
      expect(screen.getAllByTestId(suggestionTestId('En savoir plus')).length).toBeGreaterThan(0);
      expect(screen.getAllByTestId(suggestionTestId('Autre question')).length).toBeGreaterThan(0);
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
    await waitFor(() => {
      expect(screen.getAllByText(/Voici quelques suggestions|Bonjour ! Je suis l'assistant GW2 Optimizer/).length).toBeGreaterThan(0);
    });
    
    // Vérifier que les suggestions sont affichées
    await waitFor(() => {
      expect(screen.getAllByTestId(suggestionTestId('En savoir plus')).length).toBeGreaterThan(0);
      expect(screen.getAllByTestId(suggestionTestId('Autre question')).length).toBeGreaterThan(0);
    });
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
    
    // Wait for all suggestions to be present dans le DOM
    const [primarySuggestion] = await screen.findAllByTestId(suggestionTestId('En savoir plus'));
    const [secondarySuggestion] = await screen.findAllByTestId(suggestionTestId('Autre question'));
    const suggestionButtons = [primarySuggestion, secondarySuggestion];
    expect(suggestionButtons.length).toBe(2);
    
    // Click on the primary suggestion
    fireEvent.click(primarySuggestion);
    
    // Check that the input was updated with the suggestion
    const updatedInput = screen.getByPlaceholderText('Posez votre question...') as HTMLInputElement;
    expect(updatedInput.value).toBe('En savoir plus');
    
    // Send the suggestion
    // Get all send buttons again and use the first one
    const updatedSendButtons = screen.getAllByRole('button', { name: /envoyer le message/i });
    const updatedSendButton = updatedSendButtons[0];
    fireEvent.click(updatedSendButton);
    
    // Check that the API was called with the suggestion
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('En savoir plus', '1.0.0');
    });
    
    // Check that the response is displayed (duplicate instances allowed for responsive layouts)
    await waitFor(() => {
      expect(screen.getAllByText('Voici plus d\'informations').length).toBeGreaterThan(0);
    });
  });
});
