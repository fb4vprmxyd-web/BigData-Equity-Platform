"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Unit tests for quality-weighted sentiment signal
Project : CW2 - Value-Sentiment Investment Strategy

Coverage target: 85%+
"""

import numpy as np
import pandas as pd
import pytest

from modules.signals.sentiment_signal import SentimentSignal


@pytest.fixture
def config():
    return {
        'sentiment': {
            'half_life_days': 7,
            'source_tiers': {
                'tier1': ['reuters.com', 'bloomberg.com'],
                'tier2': ['cnbc.com'],
                'tier3': ['seekingalpha.com'],
            },
            'tier_weights': {'tier1': 1.0, 'tier2': 0.7, 'tier3': 0.4, 'default': 0.3},
        },
        'scoring': {
            'shrinkage_k_sentiment': 5,
            'min_sentiment_confidence': 0.3,
        },
    }


@pytest.fixture
def sample_sentiment_df():
    return pd.DataFrame({
        'company_id': ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
        'date': pd.to_datetime(['2024-01-15'] * 4),
        'avg_sentiment': [0.3, 0.1, -0.1, 0.5],
        'positive_count': [8, 5, 3, 12],
        'negative_count': [2, 4, 6, 1],
        'neutral_count': [5, 6, 6, 2],
        'total_articles': [15, 15, 15, 15],
        'positive_ratio': [0.53, 0.33, 0.20, 0.80],
        'sentiment_score': [65, 52, 40, 78],
    })


class TestSentimentSignal:

    def test_basic_scoring(self, config, sample_sentiment_df):
        signal = SentimentSignal(config)
        result = signal.compute(sample_sentiment_df, pd.Timestamp('2024-01-31'))
        assert len(result) == 4
        assert 'sentiment_score' in result.columns
        assert 'confidence' in result.columns

    def test_bayesian_shrinkage(self, config):
        """Stocks with few articles should be shrunk toward zero."""
        signal = SentimentSignal(config)
        df = pd.DataFrame({
            'company_id': ['FEW', 'MANY'],
            'date': pd.to_datetime(['2024-01-15'] * 2),
            'avg_sentiment': [0.5, 0.5],
            'total_articles': [1, 50],
            'positive_ratio': [0.8, 0.8],
            'sentiment_score': [70, 70],
        })
        result = signal.compute(df, pd.Timestamp('2024-01-31'))
        few_conf = result[result['company_id'] == 'FEW']['confidence'].iloc[0]
        many_conf = result[result['company_id'] == 'MANY']['confidence'].iloc[0]
        assert many_conf > few_conf, "More articles should give higher confidence"

    def test_confidence_range(self, config, sample_sentiment_df):
        """Confidence should be between 0 and 1."""
        signal = SentimentSignal(config)
        result = signal.compute(sample_sentiment_df, pd.Timestamp('2024-01-31'))
        assert (result['confidence'] >= 0).all()
        assert (result['confidence'] <= 1).all()

    def test_zero_articles(self, config):
        """Stocks with zero articles should have zero confidence."""
        signal = SentimentSignal(config)
        df = pd.DataFrame({
            'company_id': ['NONE'],
            'date': pd.to_datetime(['2024-01-15']),
            'avg_sentiment': [None],
            'total_articles': [0],
            'positive_ratio': [None],
            'sentiment_score': [None],
        })
        result = signal.compute(df, pd.Timestamp('2024-01-31'))
        assert result['confidence'].iloc[0] == 0.0

    def test_empty_input(self, config):
        df = pd.DataFrame(columns=['company_id', 'date', 'avg_sentiment',
                                    'total_articles', 'positive_ratio', 'sentiment_score'])
        signal = SentimentSignal(config)
        result = signal.compute(df, pd.Timestamp('2024-01-31'))
        assert len(result) == 0
