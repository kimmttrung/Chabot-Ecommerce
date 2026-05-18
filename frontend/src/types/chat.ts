export interface Message {
    id: string;
    sender: 'user' | 'bot';
    text: string;
    timestamp: Date;
}

export interface ChatSession {
    id: string;
    title: string;
    messages: Message[];
}