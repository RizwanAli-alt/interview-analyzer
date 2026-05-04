from django.core.management.base import BaseCommand
from questions.models import Domain, Question


SEED_DATA = [
    {
        "name": "Data Structures & Algorithms",
        "description": "Arrays, trees, graphs, sorting, searching",
        "icon": "diagram-3",
        "questions": [
            {
                "text": "Explain the difference between a stack and a queue. When would you use each?",
                "rubric": "Stack: LIFO, use cases (undo, call stack, DFS). Queue: FIFO, use cases (BFS, scheduling, print queue). Should mention real-world examples.",
                "level": "easy"
            },
            {
                "text": "How does a hash table work? What happens during a collision?",
                "rubric": "Hash function converts key to index. Collision resolution: chaining (linked list at bucket) or open addressing (linear/quadratic probing). Time complexity O(1) average.",
                "level": "medium"
            },
            {
                "text": "Explain the time and space complexity of merge sort. Why is it preferred over quicksort in some cases?",
                "rubric": "O(n log n) time always. O(n) space. Stable sort. Preferred for linked lists, external sorting, when stability matters. Quicksort is in-place but O(n²) worst case.",
                "level": "hard"
            },
        ]
    },
    {
        "name": "System Design",
        "description": "Scalability, databases, APIs, architecture",
        "icon": "server",
        "questions": [
            {
                "text": "How would you design a URL shortener like bit.ly?",
                "rubric": "Base62 encoding, unique ID generation, database schema (short_code, long_url, created_at), redirect logic, caching with Redis, rate limiting, analytics.",
                "level": "medium"
            },
            {
                "text": "What is the difference between SQL and NoSQL databases? When would you pick each?",
                "rubric": "SQL: ACID, relational, structured schema, joins. NoSQL: horizontal scaling, flexible schema, types (document, key-value, graph, column). Use cases for each.",
                "level": "easy"
            },
            {
                "text": "How would you design a real-time notification system for millions of users?",
                "rubric": "WebSockets vs long polling vs SSE. Message queue (Kafka/RabbitMQ). Push notification services. Fan-out strategies. Database for persistence. Horizontal scaling.",
                "level": "hard"
            },
        ]
    },
    {
        "name": "Object-Oriented Programming",
        "description": "OOP principles, design patterns, SOLID",
        "icon": "boxes",
        "questions": [
            {
                "text": "What are the four pillars of OOP? Give a real-world example for each.",
                "rubric": "Encapsulation (hiding internal state), Inheritance (reusing code via parent class), Polymorphism (same interface different behaviour), Abstraction (hiding complexity). Real examples for each.",
                "level": "easy"
            },
            {
                "text": "Explain the SOLID principles with examples.",
                "rubric": "Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Code example or analogy for each. Why they matter for maintainability.",
                "level": "medium"
            },
            {
                "text": "When would you use composition over inheritance? Give a concrete example.",
                "rubric": "Composition is more flexible, avoids deep hierarchies, avoids fragile base class problem. Example: a Car HAS-A Engine (composition) vs Car IS-A Vehicle (inheritance). Design pattern: strategy pattern.",
                "level": "hard"
            },
        ]
    },
    {
        "name": "Behavioral",
        "description": "Teamwork, problem-solving, communication",
        "icon": "people",
        "questions": [
            {
                "text": "Tell me about a time you had to debug a difficult problem. How did you approach it?",
                "rubric": "STAR format: situation, task, action, result. Should mention systematic approach, using logs/debugger, isolating variables, asking for help when needed, documenting the fix.",
                "level": "medium"
            },
            {
                "text": "Describe a time you disagreed with a team member. How was it resolved?",
                "rubric": "Professional disagreement handling: listen first, data/logic over opinion, compromise, escalation when necessary. Focus on outcome and relationship preservation.",
                "level": "medium"
            },
            {
                "text": "Tell me about a project you're proud of. What was your specific contribution?",
                "rubric": "Clear ownership, measurable impact, technical depth, what they learned, what they would do differently. Should show initiative and self-awareness.",
                "level": "easy"
            },
        ]
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample domains and questions'

    def handle(self, *args, **options):
        total_q = 0
        for domain_data in SEED_DATA:
            questions = domain_data.pop('questions')
            domain, created = Domain.objects.get_or_create(
                name=domain_data['name'],
                defaults=domain_data
            )
            action = 'Created' if created else 'Found'
            self.stdout.write(f'{action} domain: {domain.name}')

            for q_data in questions:
                q, q_created = Question.objects.get_or_create(
                    domain=domain,
                    text=q_data['text'],
                    defaults=q_data
                )
                if q_created:
                    total_q += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {total_q} new questions added.'
        ))