import numpy as np

from core.layers import *
from core.layer_utils import *


class TwoLayerNet(object):
  """
  A two-layer fully-connected neural network with ReLU nonlinearity and
  softmax loss that uses a modular layer design. We assume an input dimension
  of D, a hidden dimension of H, and perform classification over C classes.
  
  The architecure should be affine - relu - affine - softmax.

  Note that this class does not implement gradient descent; instead, it
  will interact with a separate Solver object that is responsible for running
  optimization.

  The learnable parameters of the model are stored in the dictionary
  self.params that maps parameter names to numpy arrays.
  """
  
  def __init__(self, input_dim=3*32*32, hidden_dim=100, num_classes=10,
               weight_scale=1e-3, reg=0.0):
    """
    Initialize a new network.

    Inputs:
    - input_dim: An integer giving the size of the input
    - hidden_dim: An integer giving the size of the hidden layer
    - num_classes: An integer giving the number of classes to classify
    - dropout: Scalar between 0 and 1 giving dropout strength.
    - weight_scale: Scalar giving the standard deviation for random
      initialization of the weights.
    - reg: Scalar giving L2 regularization strength.
    """
    self.params = {}
    self.reg = reg
    
    W1 = np.random.normal(0, weight_scale, (input_dim, hidden_dim))
    W2 = np.random.normal(0, weight_scale, (hidden_dim, num_classes))
    b1 = np.zeros(hidden_dim)
    b2 = np.zeros(num_classes)
    self.params['W1'] = W1
    self.params['W2'] = W2
    self.params['b1'] = b1
    self.params['b2'] = b2


  def loss(self, X, y=None):
    """
    Compute loss and gradient for a minibatch of data.

    Inputs:
    - X: Array of input data of shape (N, d_1, ..., d_k)
    - y: Array of labels, of shape (N,). y[i] gives the label for X[i].

    Returns:
    If y is None, then run a test-time forward pass of the model and return:
    - scores: Array of shape (N, C) giving classification scores, where
      scores[i, c] is the classification score for X[i] and class c.

    If y is not None, then run a training-time forward and backward pass and
    return a tuple of:
    - loss: Scalar value giving the loss
    - grads: Dictionary with the same keys as self.params, mapping parameter
      names to gradients of the loss with respect to those parameters.
    """  
    scores = None
    out1, cache1 = affine_forward(X, self.params['W1'], self.params['b1'])
    out2, cache2 = relu_forward(out1)
    scores, cache3 = affine_forward(out2, self.params['W2'], self.params['b2'])

    # If y is None then we are in test mode so just return scores
    if y is None:
      return scores
    
    loss, grads = 0, {}
    loss, dx = softmax_loss(scores, y)
    dx, dw, db = affine_backward(dx, cache3)
    grads['W2'] = dw + self.reg * self.params['W2']
    grads['b2'] = db
    dx = relu_backward(dx, cache2)
    dx, dw, db = affine_backward(dx, cache1)
    grads['W1'] = dw + self.reg * self.params['W1']
    grads['b1'] = db

    loss += 0.5 * self.reg * (np.sum(self.params['W1'] ** 2) +
                              np.sum(self.params['W2'] ** 2))
    return loss, grads


class FullyConnectedNet(object):
  """
  A fully-connected neural network with an arbitrary number of hidden layers,
  ReLU nonlinearities, and a softmax loss function. This will also implement
  dropout and batch normalization as options. For a network with L layers,
  the architecture will be
  
  {affine - [batch norm] - relu - [dropout]} x (L - 1) - affine - softmax
  
  where batch normalization and dropout are optional, and the {...} block is
  repeated L - 1 times.
  """

  def __init__(self, hidden_dims, input_dim=3*32*32, num_classes=10,
               dropout=0, use_batchnorm=False, reg=0.0,
               weight_scale=1e-2, dtype=np.float32, seed=None):
    """
    Initialize a new FullyConnectedNet.
    
    Inputs:
    - hidden_dims: A list of integers giving the size of each hidden layer.
    - input_dim: An integer giving the size of the input.
    - num_classes: An integer giving the number of classes to classify.
    - dropout: Scalar between 0 and 1 giving dropout strength. If dropout=0 then
      the network should not use dropout at all.
    - use_batchnorm: Whether or not the network should use batch normalization.
    - reg: Scalar giving L2 regularization strength.
    - weight_scale: Scalar giving the standard deviation for random
      initialization of the weights.
    - dtype: A numpy datatype object; all computations will be performed using
      this datatype. float32 is faster but less accurate, so you should use
      float64 for numeric gradient checking.
    - seed: If not None, then pass this random seed to the dropout layers. This
      will make the dropout layers deteriminstic so we can gradient check the
      model.
    """
    self.use_batchnorm = use_batchnorm
    self.use_dropout = dropout > 0
    self.reg = reg
    self.num_layers = 1 + len(hidden_dims)
    self.dtype = dtype
    self.params = {}

    # first hidden layer
    self.params['W1'] = np.random.normal(
      0,
      weight_scale,
      (input_dim,hidden_dims[0]))
    self.params['b1'] = np.zeros(hidden_dims[0])
    if self.use_batchnorm:
      self.params['gamma1'] = np.ones(hidden_dims[0])
      self.params['beta1'] = np.zeros(hidden_dims[0])

    # remaining hidden layers
    for i in range(2, len(hidden_dims) + 1):
      wname = 'W' + str(i)
      bname = 'b' + str(i)
      self.params[wname] = np.random.normal(
        0,
        weight_scale,
        (hidden_dims[i - 2], hidden_dims[i - 1]))
      self.params[bname] = np.zeros(hidden_dims[i - 1])
      if self.use_batchnorm:
        gname = 'gamma' + str(i)
        bename = 'beta' + str(i)
        self.params[gname] = np.ones(hidden_dims[i - 1])
        self.params[bename] = np.zeros(hidden_dims[i - 1])

    # remaining layers
    wname = 'W' + str(len(hidden_dims) + 1)
    bname = 'b' + str(len(hidden_dims) + 1)
    self.params[wname] = np.random.normal(
      0,
      weight_scale,
      (hidden_dims[len(hidden_dims) - 1],num_classes))
    self.params[bname] = np.zeros(num_classes)

    # When using dropout we need to pass a dropout_param dictionary to each
    # dropout layer so that the layer knows the dropout probability and the mode
    # (train / test). You can pass the same dropout_param to each dropout layer.
    self.dropout_param = {}
    if self.use_dropout:
      self.dropout_param = {'mode': 'train', 'p': dropout}
      if seed is not None:
        self.dropout_param['seed'] = seed
    
    # With batch normalization we need to keep track of running means and
    # variances, so we need to pass a special bn_param object to each batch
    # normalization layer. You should pass self.bn_params[0] to the forward pass
    # of the first batch normalization layer, self.bn_params[1] to the forward
    # pass of the second batch normalization layer, etc.
    self.bn_params = []
    if self.use_batchnorm:
      self.bn_params = [{'mode': 'train'} for i in xrange(self.num_layers - 1)]
    
    # Cast all parameters to the correct datatype
    for k, v in self.params.iteritems():
      self.params[k] = v.astype(dtype)


  def loss(self, X, y=None):
    """
    Compute loss and gradient for the fully-connected net.

    Input / output: Same as TwoLayerNet above.
    """
    X = X.astype(self.dtype)
    mode = 'test' if y is None else 'train'

    # Set train/test mode for batchnorm params and dropout param since they
    # behave differently during training and testing.
    if self.dropout_param is not None:
      self.dropout_param['mode'] = mode   
    if self.use_batchnorm:
      for bn_param in self.bn_params:
        bn_param[mode] = mode

    scores = None
    
    cachemap = {}
    regloss = 0
    nextlayerinput = X

    # first and hidden layers
    for i in range(1, self.num_layers):
      nextlayerinput, cachemap['acache'+str(i)] = affine_forward(
        nextlayerinput,
        self.params['W'+str(i)],
        self.params['b'+str(i)])
      regloss += 0.5 * self.reg * np.sum(self.params['W'+str(i)] ** 2)
      if self.use_batchnorm:
        nextlayerinput, cachemap['bcache'+str(i)] = batchnorm_forward(
          nextlayerinput,
          self.params['gamma'+str(i)],
          self.params['beta'+str(i)],
          bn_param[i-1])
      nextlayerinput, cachemap['rcache'+str(i)] = relu_forward(nextlayerinput)
      if self.use_dropout:
        nextlayerinput, cachemap['dcache'+str(i)] = dropout_forward(
            nextlayerinput,
            self.dropout_param)

    # last layer
    scores, cachemap['acache'+str(self.num_layers)] = affine_forward(
      nextlayerinput,
      self.params['W'+str(self.num_layers)],
      self.params['b'+str(self.num_layers)])
    regloss += 0.5*self.reg * np.sum(self.params['W'+str(self.num_layers)]**2)

    # If test mode return early
    if mode == 'test':
      return scores

    grads = {}
    loss, nextdout = softmax_loss(scores, y)
    loss += regloss
    
    w = 'W' + str(self.num_layers)
    b = 'b' + str(self.num_layers)
    nextdout,grads[w],grads[b] =  affine_backward(
      nextdout,
      cachemap['acache'+str(self.num_layers)])
    grads[w] += self.reg * self.params[w]

    for i in range(self.num_layers-1, 0, -1):
      if self.use_dropout:
        nextdout = dropout_backward(nextdout, cachemap['dcache'+str(i)])
      nextdout = relu_backward(nextdout, cachemap['rcache'+str(i)])
      if self.use_batchnorm:
        gamma = 'gamma' + str(i)
        beta = 'beta' + str(i)
        nextdout,grads[gamma],grads[beta] = batchnorm_backward(
          nextdout,
          cachemap['bcache'+str(i)])
      w = 'W' + str(i)
      b = 'b' + str(i)
      nextdout,grads[w],grads[b] = affine_backward(
        nextdout,
        cachemap['acache'+str(i)])
      grads[w] += self.reg * self.params[w]

    return loss, grads
