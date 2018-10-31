import argparse
import os
import time

import gym
import yaml
import numpy as np

from stable_baselines.common.cmd_util import make_atari_env
from stable_baselines.common.vec_env import VecFrameStack, SubprocVecEnv, VecNormalize
from stable_baselines.bench import Monitor
from stable_baselines import PPO2, A2C, ACER, ACKTR

def make_env(env_id, rank=0, seed=0):
  log_dir = "/tmp/gym/{}/".format(int(time.time()))
  os.makedirs(log_dir, exist_ok=True)

  def _init():
    env = gym.make(env_id)
    env.seed(seed + rank)
    env = Monitor(env, os.path.join(log_dir, str(rank)), allow_early_resets=True)
    return env

  return _init


ALGOS = {
	'a2c': A2C,
	'acer': ACER,
	'acktr': ACKTR,
	'ppo2': PPO2
}

parser = argparse.ArgumentParser()
parser.add_argument('--env', help='environment ID', type=str, default='CartPole-v1')
parser.add_argument('-tb', '--tensorboard-log', help='Tensorboard log dir', default='', type=str)
parser.add_argument('--algo', help='RL Algorithm', default='ppo2',
					type=str, required=False, choices=list(ALGOS.keys()))
parser.add_argument('-n', '--n-timesteps', help='Overwrite the number of timesteps', default=-1,
					type=int)
parser.add_argument('-f', '--log-folder', help='Log folder', type=str, default='logs')

args = parser.parse_args()

env_ids = (args.env, )

for env_id in env_ids:
    tensorboard_log = None if args.tensorboard_log == '' else args.tensorboard_log + '/' + env_id

    is_atari = False
    if 'NoFrameskip' in env_id:
        is_atari = True

    print("="*10, env_id, "="*10)

    with open('hyperparams/{}.yml'.format(args.algo), 'r') as f:
        if is_atari:
            hyperparams = yaml.load(f)['atari']
        else:
            hyperparams = yaml.load(f)[env_id]

    n_envs = hyperparams['n_envs']
    if args.n_timesteps > 0:
        n_timesteps = args.n_timesteps
    else:
        n_timesteps = int(hyperparams['n_timesteps'])

    normalize = False
    if 'normalize' in hyperparams.keys():
        normalize = hyperparams['normalize']
        del hyperparams['normalize']

    # Delete keys so the dict can be pass to the model constructor
    del hyperparams['n_envs']
    del hyperparams['n_timesteps']


    if is_atari:
        print("Using Atari wrapper")
        env = make_atari_env(env_id, num_env=n_envs, seed=0)
        # Frame-stacking with 4 frames
        env = VecFrameStack(env, n_stack=4)
    else:
        env = SubprocVecEnv([make_env(env_id, i) for i in range(n_envs)])
        if normalize:
            print("Normalizing input and return")
            env = VecNormalize(env)

    model = ALGOS[args.algo](env=env, tensorboard_log=tensorboard_log, verbose=1, **hyperparams)
    model.learn(n_timesteps)

    os.makedirs("{}/{}/".format(args.log_folder, args.algo), exist_ok=True)
    model.save("{}/{}/{}".format(args.log_folder, args.algo, env_id))
    if normalize:
        path = "{}/{}/{}".format(args.log_folder, args.algo, env_id)
        os.makedirs(path, exist_ok=True)
        # Important: save the running average, for testing the agent we need that normalization
        env.save_running_average(path)