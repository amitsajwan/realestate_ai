import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const username = formData.get('username') as string;
    const password = formData.get('password') as string;

    if (!username || !password) {
      return NextResponse.json({ error: 'Username and password required' }, { status: 400 });
    }

    // Call backend login API
    const backendResponse = await fetch('http://localhost:8000/api/v1/auth/jwt/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      return NextResponse.json({ error: 'Login failed', details: errorData }, { status: backendResponse.status });
    }

    const loginData = await backendResponse.json();
    
    return NextResponse.json({ 
      success: true, 
      message: 'Login successful',
      access_token: loginData.access_token,
      user: loginData.user || { email: username }
    });

  } catch (error) {
    console.error('Login API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}