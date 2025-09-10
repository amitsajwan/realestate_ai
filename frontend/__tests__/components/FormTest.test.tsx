import React from 'react';
import { render } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Test if react-hook-form and zod work together
const testSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
});

type TestFormData = z.infer<typeof testSchema>;

const TestForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<TestFormData>({
    resolver: zodResolver(testSchema),
  });

  const onSubmit = (data: TestFormData) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} placeholder="Name" />
      {errors.name && <span>{errors.name.message}</span>}
      
      <input {...register('email')} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}
      
      <button type="submit">Submit</button>
    </form>
  );
};

describe('Form Test', () => {
  test('renders form with react-hook-form and zod', () => {
    const { container } = render(<TestForm />);
    expect(container.firstChild).toBeInTheDocument();
  });
});