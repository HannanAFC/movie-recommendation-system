import { BasicHeader } from '../components/BasicHeader';
import { LoginForm } from '../components/LoginForm';

export function LoginPage()
{
    return (
        <>
            <title>WatchWok | Login</title>
                        
            <BasicHeader sticky={true} />
            <div className="min-h-[calc(100vh-112px)] flex flex-col items-center justify-center gap-2 md:gap-4">
                <h1 className="font-bold text-3xl md:text-4xl">
                    Login to your account
                </h1>
                <LoginForm />
            </div>
        </>
    );
}