const whatsMyOutput = obj => {
  const regex = s => s.replace(/([_][a-zA-Z0-9])/g, g => g.toUpperCase().replace('_', ''))
  const isObject = (obj) => obj === Object(obj) && !Array.isArray(obj) && typeof obj !== 'function'

  if (isObject(obj)) {
    return Object.entries(obj).reduce((prev, [key, value]) => {
      if (typeof value === 'object' && value !== null) {
        return { ...prev, [regex(key)]: whatsMyOutput(value) }
      }
      return { ...prev, [regex(key)]: value }
    }, {})
  } else if (Array.isArray(obj)) {
    return obj.map(it => whatsMyOutput(it))
  } else {
    return obj
  }
}

const input = {
  foo: 'bar',
  michael_jackson: [
    'Billie',
    'Jean',
    'is',
    'not',
    'my',
    'lover',
  ],
  AB_BA: {
    song_title: 'Dancing Queen',
    lyrics: {
      'first_part': [
        {
          text_value: 'you can dance',
        },
        {
          text_value: 'you can jive',
        },
      ],
      'second_part': [
        {
          text_value: 'You\'re a teaser, you turn \'em on',
        },
        {
          text_value: 'Leave \'em burning and then you\'re gone',
        },
      ]
    },
  },
}

const output = whatsMyOutput(input)

//console.log(JSON.stringify(output, null, 2))
