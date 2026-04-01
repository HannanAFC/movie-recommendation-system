import { BasicHeader } from '../components/BasicHeader';
import { RegisterForm } from '../components/RegisterForm';

export function RegisterPage()
{
    return (
        <>
            <title>WatchWok | Create an account</title>
                        
            <BasicHeader sticky={true} />
            <div className="min-h-[calc(100vh-112px)] flex flex-col items-center justify-center gap-2 md:gap-4">
                <h1 className="font-bold text-3xl md:text-4xl">
                    Create an account
                </h1>
                <RegisterForm />
            </div>
        </>
    );
}