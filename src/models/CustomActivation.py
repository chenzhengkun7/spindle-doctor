import numpy as np
import tensorflow as tf
from tensorflow.contrib import rnn, legacy_seq2seq

class Model:
    def __init__(self, step_size, hidden_size, embedding_size, symbol_size, layer_depth, batch_size, dropout_rate, rnn_unit, mse_weights):
        self.step_size = step_size
        self.hidden_size = hidden_size
        self.embedding_size = embedding_size
        self.symbol_size = symbol_size
        self.layer_depth = layer_depth
        self.batch_size = batch_size
        self.dropout_rate = dropout_rate
        self.mse_weights = mse_weights
        self.rnn_unit = rnn_unit

        with tf.name_scope('input_layer'):
            self.add_input_layer()

        with tf.variable_scope('embedding_layer'):
            self.add_embedding_layer()

        with tf.variable_scope('output_layer'):
            self.add_output_layer()

        with tf.name_scope('compute_cost'):
            self.compute_entropy_cost()
            self.compute_mse_cost()

        with tf.name_scope('train_step'):
            self.add_train_step()

    def add_input_layer(self):
        self.xs = tf.placeholder(
            tf.int32,
            [None, self.step_size],
            name='xs'
        )
        self.ys = tf.placeholder(
            tf.int32,
            [None, self.step_size],
            name='ys'
        )
        self.feed_previous = tf.placeholder(
            tf.bool,
            name='feed_previous'
        )
        self.learning_rate = tf.placeholder(
            tf.float32,
            name='learning_rate'
        )
        self.mse_weights = tf.constant(self.mse_weights)

    def rnn_cell(self, output_size):
        cell = None
        if self.rnn_unit == 'LSTM':
            cell = rnn.BasicLSTMCell(
                num_units=output_size,
                forget_bias=1.0,
                state_is_tuple=True,
                activation=tf.nn.sigmoid,
                reuse=tf.get_variable_scope().reuse
            )
        elif self.rnn_unit == 'GRU':
            cell = rnn.GRUCell(
                num_units=output_size,
                activation=tf.nn.sigmoid,
                reuse=tf.get_variable_scope().reuse
            )
        elif self.rnn_unit == 'BASIC-RNN':
            cell = rnn.BasicRNNCell(
                num_units=output_size,
                activation=tf.nn.sigmoid,
                reuse=tf.get_variable_scope().reuse
            )
        return rnn.DropoutWrapper(cell, input_keep_prob=1 - self.dropout_rate)

    def add_embedding_layer(self):
        self.enc_inp = tf.unstack(self.xs, axis=1)
        self.dec_inp = [np.zeros(self.batch_size, dtype=np.int) for t in range(self.step_size)]
        layers = rnn.MultiRNNCell(
            [self.rnn_cell(self.hidden_size) for i in range(self.layer_depth)],
            state_is_tuple=True
        )
        self.dec_outputs, _ = tf.contrib.legacy_seq2seq.embedding_rnn_seq2seq(
            self.enc_inp,
            self.dec_inp,
            layers,
            self.symbol_size,
            self.symbol_size,
            self.embedding_size,
            output_projection=None,
            feed_previous=self.feed_previous
        )

    def add_output_layer(self):
        # shape = [batch_size, step_size, symbol_size]
        self.outputs = tf.stack(self.dec_outputs, axis=1)

        # shape = [batch_size, step_size]
        self.prediction = tf.cast(tf.argmax(self.outputs, axis=2), tf.int32)
        correct_prediction = tf.equal(self.ys, self.prediction)

        # shape = [batch_size]
        accuracy_per_row = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), axis=1)
        self.accuracy = tf.reduce_mean(accuracy_per_row)

    def compute_entropy_cost(self):
        current_batch_size = tf.shape(self.outputs)[0]
        logits = tf.unstack(tf.cast(self.outputs, tf.float32), axis=1)
        targets = tf.unstack(self.ys, axis=1)
        weights = [
            tf.ones([current_batch_size], tf.float32)
            for _ in range(self.step_size)
        ]
        self.error = tf.contrib.legacy_seq2seq.sequence_loss(
            logits,
            targets=targets,
            weights=weights
        )

    def compute_mse_cost(self):
        self.restored_prediction = tf.reshape(
            tf.map_fn(
                lambda level: self.mse_weights[level],
                tf.reshape(self.prediction, [-1]),
                dtype=tf.float64,
            ),
            [self.batch_size, -1]
        )
        self.restored_ys = tf.reshape(
            tf.map_fn(
                lambda level: self.mse_weights[level],
                tf.reshape(self.ys, [-1]),
                dtype=tf.float64,
            ),
            [self.batch_size, -1]
        )
        self.mse_error = tf.reduce_mean(tf.square(tf.subtract(
            self.restored_ys,
            self.restored_prediction
        )))

    def add_train_step(self):
        # self.train_step = tf.train.MomentumOptimizer(self.learning_rate, 0.9).minimize(self.error)
        optimizer = tf.train.AdamOptimizer(self.learning_rate)
        grads_and_vars = optimizer.compute_gradients(self.error)
        self.gradients, variables = zip(*grads_and_vars)
        self.g0 = tf.convert_to_tensor(self.gradients[0])
        self.sg0 = tf.reduce_sum(self.g0, axis=1)
        print('=========================================')
        [print(x) for x in self.gradients]
        print('=========================================')
        # a = g[0]
        # b = tf.matmul(a, g[1])
        # print(b)
        # c = tf.matmul(b, g[2])
        # print(c)
        # print('=========================================')
        self.train_step = optimizer.apply_gradients(grads_and_vars)
        # self.train_step = tf.train.RMSPropOptimizer(self.learning_rate).minimize(self.error)