// random quotes
// Array of stress-relieving quotes
const quotes = [
    "Take a deep breath and let go of what you can't control.",
    "Slow down and appreciate the little things in life.",
    "Your peace is more important than perfection.",
    "Every day may not be good, but there's something good in every day.",
    "Smile, breathe, and go slowly.",
    "Relax, recharge, and reflect. Sometimes it’s okay to do nothing.",
    "You are enough just as you are.",
    "Inhale peace, exhale stress.",
    "Let go of what’s gone, be grateful for what remains, and look forward to what’s coming.",
    "Don't stress. Do your best and forget the rest.",
    "Take time to do what makes your soul happy.",
    "Sometimes, the most productive thing you can do is relax.",
    "Peace begins with a smile.",
    "This too shall pass.",
    "You’ve survived 100% of your bad days, and that’s pretty amazing.",
    "Do more of what makes you forget to check your phone.",
    "Rest is not idleness, it’s an investment in your wellbeing.",
    "Your mind will answer most questions if you learn to relax and wait for the answer.",
    "It’s okay to take a break and reset.",
    "You don’t have to be perfect to be amazing.",
    "Let yourself be a beginner. No one starts off being excellent."
];

// Function to display a random quote
function displayRandomQuote() {
    const quoteElement = document.getElementById('quote');
    const randomIndex = Math.floor(Math.random() * quotes.length);
    quoteElement.textContent = quotes[randomIndex];
}

// Call the function when the page loads
window.onload = displayRandomQuote;