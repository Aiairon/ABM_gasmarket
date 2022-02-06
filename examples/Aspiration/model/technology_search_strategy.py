import random
import numpy as np
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from Melodie import AgentList

if TYPE_CHECKING:
    from .agent import AspirationAgent
    from .environment import AspirationEnvironment


class TechnologySearchStrategy(ABC):

    def __init__(self, agent_list: 'AgentList[AspirationAgent]', environment: 'AspirationEnvironment'):
        self.agent_list = agent_list
        self.environment = environment

    @abstractmethod
    def technology_search(self, agent: 'AspirationAgent') -> None:
        pass


class SleepTechnologySearchStrategy(TechnologySearchStrategy):

    def technology_search(self, agent: 'AspirationAgent') -> None:
        agent.sleep_count += 1
        pass


class ExplorationTechnologySearchStrategy(TechnologySearchStrategy):

    def technology_search(self, agent: 'AspirationAgent') -> None:
        mean = self.environment.scenario.sigma_exploration
        sigma = self.environment.scenario.sigma_exploration
        technology_search_result = np.random.lognormal(mean, sigma)
        agent.technology = max(agent.technology, technology_search_result)
        agent.exploration_count += 1
        agent.account -= self.environment.scenario.cost_exploration


class ExploitationTechnologySearchStrategy(TechnologySearchStrategy):

    def technology_search(self, agent: 'AspirationAgent') -> None:
        sigma = self.environment.scenario.sigma_exploitation
        technology_search_result = np.random.normal(agent.technology, sigma)
        agent.technology = max(agent.technology, technology_search_result)
        agent.exploitation_count += 1
        agent.account -= self.environment.scenario.cost_exploitation


class ImitationTechnologySearchStrategy(TechnologySearchStrategy):

    def technology_search(self, agent: 'AspirationAgent') -> None:
        random_agent_list = random.sample(self.agent_list, int(len(self.agent_list) * self.environment.scenario.imitation_share))
        technology_search_result = np.array([item.technology for item in random_agent_list]).max()
        rand = np.random.uniform(0, 1)
        if rand <= (1 - self.environment.scenario.imitation_fail_rate):
            agent.technology = max(agent.technology, technology_search_result)
        else:
            pass
        agent.imitation_count += 1
        agent.account -= self.environment.scenario.cost_imitation

