export function formatDateToYear( date )
{
    const formatted = new Date( date )
    return formatted.getFullYear( );
}

export function formatDateFull( date )
{
    const formatted = new Date( date )
    return formatted.toLocaleDateString( "en-GB",
    {
        month: "long",
        day: "numeric",
        year: "numeric"
    } );
}