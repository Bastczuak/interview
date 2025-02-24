const axios = {
  get: () => Promise.resolve({
    data: {
      status: 'USER_NOT_EXISTS'
    }
  }),
  put: () => Promise.resolve({
    data: {
      currency: 'EUR'
    }
  })
}

const checkStatus = (acceptedStates, fn) => async function (...args) {
  const { data: { status } } = await axios.get(`/api/status/${this.supportCase.name}`)
  if (acceptedStates.includes(status)) {
    return fn.apply(this, args)
  } else {
    this.toast.error('Sorry, cannot let u do this because user not exists')
  }
}

const someObject = {
  supportCase: {
    name: 'foobar'
  },
  currency: 'USD',
  toast: {
    error(...args) {
      console.error(args)
    }
  },
  doAnApiCall: checkStatus(
    ['USER_EXISTS'], 
    async function(user, currency) {
      try {
        this.currency = (await axios.put(`/api/currency/${currency}`, user)).data.currency
      } catch (error) {
        this.toast.error(error)
      }
    }
  )
};

(async function() {
  console.log('UPDATE CURRENCY')
  // await someObject.doAnApiCall('max mustermann', 'EUR')
  console.log('DONE', someObject.currency)
})()

