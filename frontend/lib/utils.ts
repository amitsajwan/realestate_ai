import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes
 * Combines clsx for conditional classes and tailwind-merge for deduplication
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Utility function to create responsive class names
 * @param base - Base classes
 * @param responsive - Responsive classes object
 * @returns Merged class string
 */
export function responsive(
  base: string,
  responsive: {
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
    '2xl'?: string;
  }
): string {
  const classes = [base];
  
  if (responsive.sm) classes.push(`sm:${responsive.sm}`);
  if (responsive.md) classes.push(`md:${responsive.md}`);
  if (responsive.lg) classes.push(`lg:${responsive.lg}`);
  if (responsive.xl) classes.push(`xl:${responsive.xl}`);
  if (responsive['2xl']) classes.push(`2xl:${responsive['2xl']}`);
  
  return classes.join(' ');
}

/**
 * Utility function to create variant class names
 * @param base - Base classes
 * @param variants - Variant classes object
 * @param selected - Selected variant
 * @returns Merged class string
 */
export function variant<T extends string>(
  base: string,
  variants: Record<T, string>,
  selected: T
): string {
  return cn(base, variants[selected]);
}

/**
 * Utility function to create conditional class names
 * @param condition - Condition to check
 * @param trueClass - Class to apply if condition is true
 * @param falseClass - Class to apply if condition is false
 * @returns Class string
 */
export function conditional(
  condition: boolean,
  trueClass: string,
  falseClass?: string
): string {
  return condition ? trueClass : falseClass || '';
}

/**
 * Utility function to create size-based class names
 * @param size - Size value
 * @param sizeMap - Size to class mapping
 * @returns Class string
 */
export function size<T extends string>(
  size: T,
  sizeMap: Record<T, string>
): string {
  return sizeMap[size] || '';
}

/**
 * Utility function to create color-based class names
 * @param color - Color value
 * @param colorMap - Color to class mapping
 * @returns Class string
 */
export function color<T extends string>(
  color: T,
  colorMap: Record<T, string>
): string {
  return colorMap[color] || '';
}

/**
 * Utility function to create spacing class names
 * @param spacing - Spacing value
 * @param direction - Direction (p, m, px, py, etc.)
 * @returns Class string
 */
export function spacing(
  spacing: number | string,
  direction: 'p' | 'm' | 'px' | 'py' | 'pt' | 'pr' | 'pb' | 'pl' | 'mt' | 'mr' | 'mb' | 'ml' = 'p'
): string {
  return `${direction}-${spacing}`;
}

/**
 * Utility function to create typography class names
 * @param scale - Typography scale
 * @returns Class string
 */
export function typography(scale: string): string {
  return `text-${scale}`;
}

/**
 * Utility function to create shadow class names
 * @param shadow - Shadow scale
 * @returns Class string
 */
export function shadow(shadow: string): string {
  return `shadow-${shadow}`;
}

/**
 * Utility function to create border radius class names
 * @param radius - Border radius scale
 * @returns Class string
 */
export function radius(radius: string): string {
  return `rounded-${radius}`;
}

/**
 * Utility function to create focus ring class names
 * @param color - Focus ring color
 * @returns Class string
 */
export function focusRing(color: string = 'primary'): string {
  return `focus:ring-${color}-500 focus:ring-2 focus:ring-offset-2`;
}

/**
 * Utility function to create hover effect class names
 * @param effect - Hover effect type
 * @returns Class string
 */
export function hover(effect: 'lift' | 'glow' | 'scale' | 'opacity'): string {
  const effects = {
    lift: 'hover:-translate-y-1 hover:shadow-md',
    glow: 'hover:shadow-lg hover:shadow-primary-500/25',
    scale: 'hover:scale-105',
    opacity: 'hover:opacity-80',
  };
  return effects[effect];
}

/**
 * Utility function to create transition class names
 * @param properties - Transition properties
 * @returns Class string
 */
export function transition(properties: string[] = ['all']): string {
  return `transition-${properties.join('-')}`;
}

/**
 * Utility function to create animation class names
 * @param animation - Animation type
 * @returns Class string
 */
export function animate(animation: string): string {
  return `animate-${animation}`;
}

/**
 * Utility function to create responsive grid class names
 * @param cols - Grid columns configuration
 * @returns Class string
 */
export function grid(cols: {
  default?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  '2xl'?: number;
}): string {
  const classes = [];
  
  if (cols.default) classes.push(`grid-cols-${cols.default}`);
  if (cols.sm) classes.push(`sm:grid-cols-${cols.sm}`);
  if (cols.md) classes.push(`md:grid-cols-${cols.md}`);
  if (cols.lg) classes.push(`lg:grid-cols-${cols.lg}`);
  if (cols.xl) classes.push(`xl:grid-cols-${cols.xl}`);
  if (cols['2xl']) classes.push(`2xl:grid-cols-${cols['2xl']}`);
  
  return classes.join(' ');
}

/**
 * Utility function to create flex class names
 * @param direction - Flex direction
 * @param align - Align items
 * @param justify - Justify content
 * @param wrap - Flex wrap
 * @returns Class string
 */
export function flex(
  direction: 'row' | 'col' = 'row',
  align: 'start' | 'center' | 'end' | 'stretch' = 'center',
  justify: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly' = 'start',
  wrap: 'wrap' | 'nowrap' | 'wrap-reverse' = 'nowrap'
): string {
  const classes = ['flex'];
  
  classes.push(`flex-${direction}`);
  classes.push(`items-${align}`);
  classes.push(`justify-${justify}`);
  classes.push(`flex-${wrap}`);
  
  return classes.join(' ');
}

/**
 * Utility function to create position class names
 * @param position - Position type
 * @param top - Top position
 * @param right - Right position
 * @param bottom - Bottom position
 * @param left - Left position
 * @returns Class string
 */
export function position(
  position: 'static' | 'relative' | 'absolute' | 'fixed' | 'sticky',
  top?: number | string,
  right?: number | string,
  bottom?: number | string,
  left?: number | string
): string {
  const classes = [`${position}`];
  
  if (top !== undefined) classes.push(`top-${top}`);
  if (right !== undefined) classes.push(`right-${right}`);
  if (bottom !== undefined) classes.push(`bottom-${bottom}`);
  if (left !== undefined) classes.push(`left-${left}`);
  
  return classes.join(' ');
}

/**
 * Utility function to create z-index class names
 * @param z - Z-index value
 * @returns Class string
 */
export function zIndex(z: number | string): string {
  return `z-${z}`;
}

/**
 * Utility function to create overflow class names
 * @param overflow - Overflow type
 * @param axis - Axis (x, y, or both)
 * @returns Class string
 */
export function overflow(
  overflow: 'auto' | 'hidden' | 'visible' | 'scroll',
  axis?: 'x' | 'y'
): string {
  if (axis) {
    return `overflow-${axis}-${overflow}`;
  }
  return `overflow-${overflow}`;
}

/**
 * Utility function to create display class names
 * @param display - Display type
 * @returns Class string
 */
export function display(display: string): string {
  return `inline-${display}`;
}