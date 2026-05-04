from django.db import models


class Domain(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='code')  # Bootstrap icon name

    def __str__(self):
        return self.name


class Question(models.Model):
    LEVEL_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    rubric = models.TextField(
        help_text='Key points a good answer should cover. Used by the AI grader.'
    )
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.domain.name} / {self.level}] {self.text[:60]}"

    class Meta:
        ordering = ['domain', 'level']