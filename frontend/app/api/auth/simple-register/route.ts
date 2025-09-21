import { NextRequest, NextResponse } from 'next/server';

/**
 * Simple Register API Route
 * ========================
 * Handles form-based registration and returns JWT token
 */

export async function POST(request: NextRequest) {
  try {
    // Get form data
    const formData = await request.formData();
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    const confirmPassword = formData.get('confirmPassword') as string;
    const firstName = formData.get('first_name') as string;
    const lastName = formData.get('last_name') as string;

    if (!email || !password || !firstName || !lastName) {
      return NextResponse.json(
        { error: 'All fields are required' },
        { status: 400 }
      );
    }

    if (password !== confirmPassword) {
      return NextResponse.json(
        { error: 'Passwords do not match' },
        { status: 400 }
      );
    }

    // Call backend register API
    const backendResponse = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      return NextResponse.json(
        { error: 'Registration failed', details: errorData },
        { status: backendResponse.status }
      );
    }

    // Get the response data
    const registerData = await backendResponse.json();
    
    // Create response
    const response = NextResponse.json(
      { 
        success: true, 
        message: 'Registration successful',
        user: registerData
      },
      { status: 200 }
    );

    // Set HTTP-only cookie with JWT token if provided
    if (registerData.access_token) {
      response.cookies.set('auth_token', registerData.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      });
    }

    return response;

  } catch (error) {
    console.error('Registration API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}