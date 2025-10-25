import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect } from 'vitest';
import { BuildGroupCard } from '../BuildGroupCard';

describe('BuildGroupCard', () => {
  const mockBuild = {
    id: 'test-build-1',
    name: 'Test Build',
    profession: 'Guardian',
    role: 'Heal',
    weapons: {
      mainHand: 'Bâton',
      offHand: 'Focus'
    },
    traits: ['Honor', 'Virtues', 'Dragonhunter'],
    skills: ['Soin de la pureté', 'Bouclier de colère', 'Sceau de protection'],
    stats: {
      healing: 1500,
      toughness: 1200,
      vitality: 1000
    }
  };

  it('affiche correctement les informations du build', () => {
    render(<BuildGroupCard build={mockBuild} playerCount={1} />);
    
    // Vérifie que le nom du build est affiché
    expect(screen.getByText('Test Build')).toBeInTheDocument();
    
    // Vérifie que la profession et le rôle sont affichés
    expect(screen.getByText('Guardian')).toBeInTheDocument();
    expect(screen.getByText('Heal')).toBeInTheDocument();
    
    // Vérifie que les armes sont affichées
    expect(screen.getByText('Bâton')).toBeInTheDocument();
    expect(screen.getByText('Focus')).toBeInTheDocument();
    
    // Vérifie que les traits sont affichés
    expect(screen.getByText('Honor')).toBeInTheDocument();
    expect(screen.getByText('Virtues')).toBeInTheDocument();
    expect(screen.getByText('Dragonhunter')).toBeInTheDocument();
    
    // Vérifie que les compétences sont affichées
    expect(screen.getByText('Soin de la pureté')).toBeInTheDocument();
    
    // Vérifie que les statistiques sont affichées
    expect(screen.getByText('Robustesse:')).toBeInTheDocument();
    expect(screen.getByText('1200')).toBeInTheDocument();
    expect(screen.getByText('Vitalité:')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
  });

  it('affiche le nombre de joueurs quand supérieur à 1', () => {
    render(<BuildGroupCard build={mockBuild} playerCount={3} />);
    
    // Vérifie que le compteur de joueurs est affiché
    expect(screen.getByText('x3')).toBeInTheDocument();
  });

  it('gère correctement les builds sans arme à deux mains', () => {
    const buildWithoutTwoHanded = {
      ...mockBuild,
      weapons: {
        mainHand: 'Épée',
        offHand: 'Bouclier'
      }
    };
    
    render(<BuildGroupCard build={buildWithoutTwoHanded} playerCount={1} />);
    
    // Vérifie que les armes sont correctement affichées
    expect(screen.getByText('Épée')).toBeInTheDocument();
    expect(screen.getByText('Bouclier')).toBeInTheDocument();
  });

  it('affiche correctement les builds avec arme à deux mains', () => {
    const buildWithTwoHanded = {
      ...mockBuild,
      weapons: {
        twoHanded: 'Bâton'
      }
    };
    
    render(<BuildGroupCard build={buildWithTwoHanded} playerCount={1} />);
    
    // Vérifie que l'arme à deux mains est affichée
    expect(screen.getByText('Bâton')).toBeInTheDocument();
  });

  it('affiche un nombre limité de traits avec un indicateur de plus', () => {
    const buildWithManyTraits = {
      ...mockBuild,
      traits: ['Trait 1', 'Trait 2', 'Trait 3', 'Trait 4', 'Trait 5']
    };
    
    render(<BuildGroupCard build={buildWithManyTraits} playerCount={1} />);
    
    // Vérifie que seuls 3 traits sont affichés
    expect(screen.getByText('Trait 1')).toBeInTheDocument();
    expect(screen.getByText('Trait 2')).toBeInTheDocument();
    expect(screen.getByText('Trait 3')).toBeInTheDocument();
    
    // Vérifie que l'indicateur "+X" est affiché
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('gère correctement les builds sans statistiques', () => {
    const buildWithoutStats = {
      ...mockBuild,
      stats: {}
    };
    
    render(<BuildGroupCard build={buildWithoutStats} playerCount={1} />);
    
    // Vérifie que la section des statistiques n'est pas affichée
    expect(screen.queryByText('Statistiques')).not.toBeInTheDocument();
  });
});
