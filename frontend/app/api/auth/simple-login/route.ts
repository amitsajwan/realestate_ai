import { NextRequest, NextResponse } from 'next/server';

/**
 * Simple Login API Route
 * =====================
 * Handles form-based login and returns JWT token
 */

export async function POST(request: NextRequest) {
  try {
    // Get form data
    const formData = await request.formData();
    const username = formData.get('username') as string;
    const password = formData.get('password') as string;

    if (!username || !password) {
      return NextResponse.json(
        { error: 'Username and password are required' },
        { status: 400 }
      );
    }

    // Call backend login API
    const backendResponse = await fetch('http://localhost:8000/api/v1/auth/jwt/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password,
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      return NextResponse.json(
        { error: 'Login failed', details: errorData },
        { status: backendResponse.status }
      );
    }

    // Get the response data
    const loginData = await backendResponse.json();
    
    // Create response with token
    const response = NextResponse.json(
      { 
        success: true, 
        message: 'Login successful',
        user: loginData.user || { email: username }
      },
      { status: 200 }
    );

    // Set HTTP-only cookie with JWT token
    if (loginData.access_token) {
      response.cookies.set('auth_token', loginData.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      });
    }

    return response;

  } catch (error) {
    console.error('Login API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}