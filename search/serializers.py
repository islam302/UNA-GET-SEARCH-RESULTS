from rest_framework import serializers
from .models import SearchWord, SearchResult

class SearchWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchWord
        fields = ['id', 'word', 'created_at']

class SearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchResult
        fields = ['id', 'search_word', 'link', 'link_text', 'created_at']
