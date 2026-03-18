import { BasicHeader } from '../components/BasicHeader';
import { LoginLink } from '../components/LoginLink';
import { RegisterLink } from '../components/RegisterLink';

export function HomePage( )
{
    return (
        <>
            <title>WatchWok | Get Started</title>
            
            <BasicHeader />

            <div className="md:min-h-[calc(100vh-112px)] flex flex-col md:grid grid-cols-2 gap-8 md:gap-2 items-center justify-center">
                <div className="flex flex-col gap-4 md:p8 p-4 rounded-2xl dark:bg-willow-green-900 bg-willow-green-200 shadow-s">
                    <h2 className="text-4xl md:text-5xl font-bold">
                        Find your next <span className="text-willow-green-500">big watch</span>
                    </h2>
                    <p className="md:text-xl">
                        WatchWok is designed to provide you with the most accurate movie recommendations, no matter your preferences.
                    </p>
                    <p className="md:text-xl">
                        Our algorithm uses filtering methods that are designed around your personal ratings of films; the more you rate, the more accurate the predictions!
                    </p>

                    <div className="flex flex-row gap-4">
                        <LoginLink />
                        <RegisterLink />
                    </div>
                </div>
                <picture>
                    <source media="(width < 769px)" srcSet="https://placehold.co/400x400" />
                    <source media="(width >= 769px)" srcSet="https://placehold.co/500x500 1x, https://placehold.co/1000x1000 2x" />
                    <img className="w-full md:max-h-[calc(100vh-112px)]" src="https://placehold.co/1000x1000" alt="WatchWork Dashboard" />
                </picture>
            </div>
        </>
    );
}