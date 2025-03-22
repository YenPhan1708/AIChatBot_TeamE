class AgentConnector:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_name, handler_function):
        self.agents[agent_name] = handler_function

    def get_agent(self, agent_name):
        return self.agents.get(agent_name)

    def process_request(self, agent_name, user_input, session_id=None):
        agent = self.get_agent(agent_name)
        if agent:
            return agent(user_input, session_id)
        return "Agent not found"