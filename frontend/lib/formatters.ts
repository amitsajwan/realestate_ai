export const formatPrice = (price?: number | null): string => {
  if (price == null || price === 0) return 'Contact for price'

  if (price >= 10000000) {
    return `₹${(price / 10000000).toFixed(1)}Cr`
  } else if (price >= 100000) {
    return `₹${(price / 100000).toFixed(0)}L`
  } else {
    return `₹${price.toLocaleString()}`
  }
}

export const formatStatusLabel = (status?: string | null): string => {
  if (!status) return 'UNKNOWN'
  const s = status.toString().toLowerCase()
  switch (s) {
    case 'for-sale':
    case 'forsale':
      return 'FOR SALE'
    case 'for-rent':
    case 'forrent':
      return 'FOR RENT'
    case 'sold':
      return 'SOLD'
    default:
      return String(status).toUpperCase()
  }
}

export default formatPrice
