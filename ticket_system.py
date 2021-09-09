from collections import deque
from enum import Enum

COMMENTS = {
    "check-wallet-balance": "sent automatic SMS to customer",
    "change-language": "automatic IVR call made to the customer"
}
TICKETS = {}
COUNTER = 0


class TicketState(Enum):
    """
    Enum class to store all Ticket States.
    """

    OPEN = 'open'
    AUTO_RESOLVED = 'auto-resolved'
    RESOLVED = 'resolved'
    ASSIGNED = 'assigned'
    CLOSED = 'resolution-verified'


class Ticket(object):
    """
    Ticket Class
    """

    def __init__(self, ticket_type, description=None):
        self.state = self.get_initial_state(ticket_type)
        self.ticket_type = ticket_type
        self.description = description
        self.resolved_by = None
        self.verified_by = None
        self.id = self.generate_id()
        self.comment = self.get_comment(ticket_type, description)

    @staticmethod
    def find_if_auto_resolved(ticket_type):
        """
        Return True if ticket has pre-defined action.
        :param ticket_type:
        :return:
        """

        return True if ticket_type in ['check-wallet-balance', 'change-language'] \
            else False

    @staticmethod
    def generate_id():
        """
        Returns Unique Ticket ID.
        :return:
        """

        global COUNTER
        COUNTER += 1
        return COUNTER

    @staticmethod
    def get_comment(ticket_type, description):
        """
        Returns Comment of ticket on the basis of ticket type.
        For ticket_type - 'others', comment will be same as description.
        :param ticket_type:
        :param description:
        :return:
        """
        if ticket_type in ['check-wallet-balance', 'change-language']:
            return COMMENTS[ticket_type]
        return description

    @staticmethod
    def get_initial_state(ticket_type):
        """
        Returns the Initial State of Ticket.
        :param ticket_type:
        :return:
        """
        if ticket_type in ['check-wallet-balance', 'change-language']:
            return TicketState.AUTO_RESOLVED
        return TicketState.OPEN


class Base(object):
    """
    Base class for Workers.
    """
    def __init__(self, name):
        self.name = name
        self.ticket = None

    def __str__(self):
        return self.name


class Employee(Base):
    """
    Employee Class
    """
    def __init__(self, name):
        super(Employee, self).__init__(name)


class Supervisor(Base):
    """
    Supervisor Class
    """
    def __init__(self, name):
        super(Supervisor, self).__init__(name)


class TicketSystem(object):
    """
    Ticket System Class
    """

    def __init__(self, employees, supervisors):
        self.employees = employees
        self.supervisors = supervisors
        self.open_ticket_queue = deque()
        self.verification_ticket_queue = deque()

    def create_ticket(self, operation_list):
        """
        Creates the ticket and pushes the newly created
        ticket to open tickets queue.
        :param operation_list:
        :return:
        """
        if operation_list[1] in ['check-wallet-balance', 'change-language']:
            ticket = Ticket(operation_list[1])
            TICKETS[ticket.id] = ticket
            print(ticket.id)
        elif operation_list[1] == 'others':
            description = ""
            for x in range(2, len(operation_list)):
                description = description + operation_list[x] + " "
            ticket = Ticket(operation_list[1], description)
            TICKETS[ticket.id] = ticket
            self.open_ticket_queue.append(ticket)
            print(ticket.id)
        else:
            print("Error! Invalid Ticket Type.")

    @staticmethod
    def get_status(operation_list):
        """
        Returns Current Status of Ticket.
        :param operation_list:
        :return:
        """

        try:
            ticket_id = int(operation_list[1])
        except Exception:
            print("Error! Invalid format of ticket Id-{}".format(operation_list[1]))
            return

        ticket = TICKETS.get(ticket_id)
        if not ticket:
            print("Error! No Ticket defined with this Id: {}".format(operation_list[1]))
            return

        print("Ticket-{} status: {} comment: {} resolved_by: {} verified_by: "
              "{}".format(ticket.id, ticket.state.value, ticket.comment,
                          ticket.resolved_by, ticket.verified_by))

    def assign_ticket(self, operation_list):
        """
        Assigns ticket to the Workers.
        :param operation_list:
        :return:
        """

        is_assigned = False
        for employee, ticket in self.employees.items():
            if employee.name == operation_list[1]:
                if not ticket:
                    for each in self.open_ticket_queue:
                        if not each.resolved_by:
                            print("Ticket: {} -> {}".format(each.id, employee.name))
                            each.resolved_by = employee
                            each.state = TicketState.ASSIGNED
                            self.employees[employee] = each
                            is_assigned = True

        if not is_assigned:
            for supervisor, ticket in self.supervisors.items():
                if supervisor.name == operation_list[1]:
                    if not ticket:
                        for each in self.verification_ticket_queue:
                            if each.resolved_by and each.state == TicketState.RESOLVED:
                                print("Ticket: {} -> {}".format(each.id, supervisor.name))
                                self.supervisors[supervisor] = each
                                each.verified_by = supervisor
                                is_assigned = True

        if not is_assigned:
            print("No Open Tickets found for {}.".format(operation_list[1]))

    def resolve_ticket(self, operation_list):
        """
        Marks the ticket as Resolved.
        :param operation_list:
        :return:
        """

        ticket = None
        for key, value in self.employees.items():
            if key.name == operation_list[1]:
                ticket = value
        if not ticket:
            print("Error! {} has no ticket assigned to "
                  "him.".format(operation_list[1]))
            return

        comment = ""
        for x in range(2, len(operation_list)):
            comment = comment + operation_list[x] + " "
        ticket.comment = comment

        ticket.state = TicketState.RESOLVED
        self.verification_ticket_queue.append(ticket)
        print("Ticket-{} resolved by {} with comment "
              "{}".format(ticket.id, operation_list[1],
                          ticket.comment))

    def verify_ticket(self, operation_list):
        """
        Marks the ticket as Resolution Verified.
        :param operation_list:
        :return:
        """

        ticket = None
        for key, value in self.supervisors.items():
            if key.name == operation_list[1]:
                ticket = value
        if not ticket:
            print("Error! {} has no ticket assigned to "
                  "him.".format(operation_list[1]))
            return

        ticket.state = TicketState.RESOLVED
        print("Ticket-{} resolution verified by supervisor "
              "{}".format(ticket.id, operation_list[1]))

    @staticmethod
    def get_all_ticket_status():
        """
        Prints total count of tickets in all statuses.
        :return:
        """

        open_count = 0
        assigned_count = 0
        closed_count = 0
        for ticket_id, ticket in TICKETS.items():
            if ticket.state in [TicketState.CLOSED, TicketState.AUTO_RESOLVED,
                                TicketState.RESOLVED]:
                closed_count += 1
            elif ticket.state == TicketState.ASSIGNED:
                assigned_count += 1
            elif ticket.state == TicketState.OPEN:
                open_count += 1

        print("{} - OPEN TICKETS".format(open_count+assigned_count))
        print("{} - ASSIGNED TICKETS".format(assigned_count))
        print("{} - CLOSED TICKETS".format(closed_count))
        print("{} - TOTAL TICKETS".format(open_count+assigned_count+closed_count))


def main():

    employees = {
        Employee("tom"): None,
        Employee("bob"): None
    }
    supervisors = {
        Supervisor("sam"): None,
        Supervisor("neil"): None
    }
    ticket_system = TicketSystem(employees, supervisors)

    while True:
        operation = input()
        operation = str(operation)

        operation_list = [each.strip() for each in operation.split(' ')]
        if operation_list and operation_list[0] == 'create-ticket':
            ticket_system.create_ticket(operation_list)

        elif operation_list and operation_list[0] == 'status':
            if len(operation_list) == 1:
                ticket_system.get_all_ticket_status()
            else:
                ticket_system.get_status(operation_list)

        elif operation_list and operation_list[0] == 'assign-ticket':
            ticket_system.assign_ticket(operation_list)

        elif operation_list[0] == 'resolve-ticket':
            ticket_system.resolve_ticket(operation_list)

        elif operation_list[0] == 'verify-ticket-resolution':
            ticket_system.verify_ticket(operation_list)

        elif operation_list[0] == "exit":
            print("Program Exited")
            break


if __name__ == "__main__":
    main()
