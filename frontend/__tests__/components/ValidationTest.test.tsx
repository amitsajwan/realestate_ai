import React from 'react';
import { render } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { propertySchema, PropertyFormData, stepSchemas } from '@/lib/validation';

// Test if the validation schema works
const TestValidationForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
  });

  const onSubmit = (data: PropertyFormData) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('title')} placeholder="Title" />
      {errors.title && <span>{errors.title.message}</span>}
      
      <input {...register('price', { valueAsNumber: true })} placeholder="Price" type="number" />
      {errors.price && <span>{errors.price.message}</span>}
      
      <button type="submit">Submit</button>
    </form>
  );
};

describe('Validation Test', () => {
  test('renders form with property validation schema', () => {
    const { container } = render(<TestValidationForm />);
    expect(container.firstChild).toBeInTheDocument();
  });

  test('stepSchemas are defined', () => {
    expect(stepSchemas).toBeDefined();
    expect(stepSchemas.address).toBeDefined();
    expect(stepSchemas.basic).toBeDefined();
    expect(stepSchemas.pricing).toBeDefined();
    expect(stepSchemas.images).toBeDefined();
    expect(stepSchemas.description).toBeDefined();
  });
});