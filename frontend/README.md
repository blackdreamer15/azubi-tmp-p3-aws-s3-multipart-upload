# S3 Upload Frontend (React)

A modern React frontend for the S3 Multipart Upload system with AWS Cognito authentication.

## Features

- 🔐 **AWS Cognito Authentication** - Secure user registration, login, and email confirmation
- 📁 **File Upload** - Drag and drop file upload with validation
- 🎨 **Modern UI** - Built with React, TypeScript, and Tailwind CSS
- 🔒 **Role-Based Access Control** - Different permissions for admin, uploader, and viewer roles
- 📱 **Responsive Design** - Works on desktop and mobile devices
- ⚡ **Fast Development** - Built with Vite for lightning-fast development

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Form handling and validation
- **React Hot Toast** - Beautiful toast notifications
- **Lucide React** - Beautiful icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (FastAPI or Next.js)

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API endpoint
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# AWS Configuration (if needed for direct client access)
VITE_AWS_REGION=us-east-1
VITE_BUCKET_NAME=your-s3-bucket-name
```

## Project Structure

```
src/
├── components/          # React components
│   ├── auth/           # Authentication components
│   └── upload/         # File upload components
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── App.tsx             # Main app component
└── main.tsx            # App entry point
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Authentication Flow

1. **Registration** - Users can register with email, password, and role
2. **Email Confirmation** - Users must confirm their email address
3. **Login** - Users can login with email and password
4. **Token Management** - Automatic token refresh and storage
5. **Role-Based Access** - Different UI based on user permissions

## User Roles

- **Admin** - Full access (upload, view, admin, delete)
- **Uploader** - Can upload and view files
- **Viewer** - Can only view files

## File Upload Features

- **Drag & Drop** - Intuitive file selection
- **File Validation** - Size, type, and security validation
- **Progress Tracking** - Real-time upload progress
- **Error Handling** - Comprehensive error messages
- **Resumable Uploads** - Support for large file uploads

## Styling

The app uses Tailwind CSS with a custom AWS-inspired color palette:

- **AWS Orange** - `#FF9900`
- **AWS Dark Blue** - `#232F3E`
- **AWS Light Blue** - `#4A90E2`
- **AWS Squid Ink** - `#161E2D`

## Development

### Adding New Components

1. Create component in appropriate directory
2. Export from index file
3. Import and use in parent component

### Adding New Hooks

1. Create hook in `src/hooks/`
2. Follow naming convention `use[Name]`
3. Export and use in components

### Styling Guidelines

- Use Tailwind CSS classes
- Follow the established color palette
- Use the `cn()` utility for conditional classes
- Keep components responsive

## Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Static Hosting

The built files in `dist/` can be deployed to any static hosting service:

- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

### Environment Configuration

Make sure to set the correct `VITE_API_BASE_URL` for your production backend.

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Write meaningful commit messages
4. Test your changes thoroughly

## License

MIT License - see LICENSE file for details.
