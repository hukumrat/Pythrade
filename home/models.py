from django.db import models

class coin_symbol(models.Model):
    def __str__(self):
        return self.symbol
    
    symbol = models.CharField(max_length=10, verbose_name="Coin Sembolü")

    class Meta:
        verbose_name = 'Kripto Para Sembolü'
        verbose_name_plural = 'Kripto Para Sembolleri'
