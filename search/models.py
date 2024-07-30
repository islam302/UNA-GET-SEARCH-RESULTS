from django.db import models

class SearchWord(models.Model):
    word = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.word

class SearchResult(models.Model):
    search_word = models.ForeignKey(SearchWord, on_delete=models.CASCADE)
    link = models.URLField()
    link_text = models.TextField(blank=True)

    def __str__(self):
        return self.link
