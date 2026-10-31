import { roomName } from '@/components/site/Plans3D'

describe('roomName', () => {
  it('reads a plan\'s capitals as words', () => {
    expect(roomName('BEDROOM -02')).toBe('Bedroom 2')
    expect(roomName('M.TOILET')).toBe('M. Toilet')
    expect(roomName('LIVING/DINING')).toBe('Living/Dining')
    expect(roomName('DECK-01')).toBe('Deck 1')
  })
})
