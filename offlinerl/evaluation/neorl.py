import multiprocessing
import gym
import ray
from copy import deepcopy
import numpy as np
from collections import OrderedDict

from offlinerl.utils.env import get_env


@ray.remote(num_gpus=1)
def test_one_trail(env, policy):
    # env = deepcopy(env)
    # policy = deepcopy(policy)

    state, done = env.reset(), False
    rewards = 0
    lengths = 0
    while not done:
        state = state[np.newaxis]
        action = policy.get_action(state).reshape(-1)
        state, reward, done, _ = env.step(action)
        rewards += reward
        lengths += 1

    return (rewards, lengths)

def test_one_trail_sp_local(env, policy):
    # env = deepcopy(env)
    # policy = deepcopy(policy)

    state, done = env.reset(), False
    rewards = 0
    lengths = 0
    act_dim = env.action_space.shape[0]
#     print("Expected action shape: " + str(env.action_space.shape))
    
    while not done:
        state = state
        action = policy.get_action(state)
#         print("Before: " + str(action.shape))
        action = action.reshape(act_dim)
#         print("After: " + str(action.shape))
        # print("actions: ", action[0:3,])
        state, reward, done, _ = env.step(action)
        rewards += reward
        lengths += 1

    return (rewards, lengths)

def test_on_real_env(policy, env, number_of_runs=100):
    rewards = []
    episode_lengths = []
    policy = deepcopy(policy)
    policy.eval()
    
    if "sp" or "sales" in env._name:
        results = [test_one_trail_sp_local(env, policy) for _ in range(number_of_runs)]
    else:
        results = ray.get([test_one_trail.remote(env, policy) for _ in range(number_of_runs)])
    # results = ray.get([test_one_trail.remote(env, policy) for _ in range(number_of_runs)])
    policy.train()
    
    rewards = [result[0] for result in results]
    episode_lengths = [result[1] for result in results]
    
    rew_mean = np.mean(rewards)
    len_mean = np.mean(episode_lengths)

    res = OrderedDict()
    res["Reward_Mean_Env"] = rew_mean
    res["Length_Mean_Env"] = len_mean

    return res
