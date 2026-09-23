def get_weather(city: str):
    mock_data_weather = {
        'Tbilisi': {'condition': 'Sunny', 'temperature_c': 25},
        'New-York': {'condition': 'Rainy', 'temperature_c': 20},
        'Baku': {'condition': 'Sunny', 'temperature_c': 26},
    }

    result = mock_data_weather.get(city, {'condition': 'Unknown', 'temperature_c': None})

    return result

def search_news(topic: str):
    return f'Some news about {topic}'


weather_tool_schema = {
    'name': 'get_weather',
    'description': 'Get current weather condition for a given city',
    'parameters': {
        'type': 'object',
        'properties': {
            'city': {
                'type': 'string',
                'description': 'The name of the city, e.g. Tbilisi'
            }
        },
        'required': ['city']
    }
}

news_tool_schema = {
    'name': 'search_news',
    'description': 'Search news about given topic',
    'parameters': {
        'type': 'object',
        'properties': {
            'topic': {
                'type': 'string',
                'description': 'Topic to search news for.'
            }
        },
        'required': ['topic']
    }
}