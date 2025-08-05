from django.db import models

class Region(models.Model):
    """Stores country/region data for phone numbers"""
    code = models.CharField(max_length=100, unique=True)  # e.g. 'IN', 'US'
    name = models.CharField(max_length=200)            # e.g. 'India'
    calling_code = models.CharField(max_length=100)      # e.g. '+91'
    # flag_emoji = models.CharField(max_length=5)        # e.g. '🇮🇳'

    class Meta:
        verbose_name = "Phone Region"
        verbose_name_plural = "Phone Regions"

    def __str__(self):
        return f" {self.name} (+{self.calling_code})"
    
    
class Country(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class State(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('code', 'country')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.country}"

class City(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('code', 'state')
        verbose_name_plural = "Cities"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.state}"