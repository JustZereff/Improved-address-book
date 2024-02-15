import json
from collections import UserDict
from datetime import datetime
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion


# Код еще немного сырой, ну вообщем вроде работает


# Определение класса поля
class Field:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return str(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

# Класс для имени
class Name(Field):
    pass

# Класс для телефона
class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        self.validate_phone()

    # Проверка на корректность номера телефона
    def validate_phone(self):
        if not (isinstance(self._value, str) and all(c.isdigit() for c in self._value) and len(self._value) == 10):
            raise ValueError("Неправильный формат записи")

# Класс для дня рождения
class Birthday:
    def __init__(self, date):
        try:
            self.birthday_date = datetime.strptime(date, "%d.%m.%Y")
        except ValueError as e:
            raise ValueError("Неправильный формат дня рождения. Ожидаемый формат - dd.mm.yyyy.") from e

    def __call__(self):
        return self.birthday_date

# Класс записи контакта
class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday else None

    # Добавление номера телефона
    def add_phone(self, phone_or_birthday):
        if isinstance(phone_or_birthday, str):  # Если передан телефон
            self.phones.append(Phone(phone_or_birthday))
        elif isinstance(phone_or_birthday, Birthday):  # Если передан день рождения
            self.birthday = phone_or_birthday
        else:
            raise ValueError("Некорректный тип данных")

    # Изменение номера телефона
    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                break
            else:
                raise ValueError

    # Поиск номера телефона
    def find_phone(self, phone):
        for record_phone in self.phones:
            if str(record_phone) == phone:
                return record_phone
        return None

    # Удаление номера телефона
    def remove_phone(self, phone):
        for phones in self.phones:
            if str(phones) == phone:
                self.phones.remove(phones)

    # Функция подсчета дней до дня рождения
    def days_to_birthday(self):
        if not self.birthday:
            return None
        current_date = datetime.now()
        next_birthday = self.birthday().replace(year=current_date.year)
        if current_date > next_birthday:
            next_birthday = next_birthday.replace(year=current_date.year + 1)
        days_until_birthday = (next_birthday - current_date).days
        return days_until_birthday

    def __str__(self):
        return f"Имя контакта: {self.name.value}, телефоны: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    def __init__(self, records_per_page=5):
        super().__init__()
        self.records_per_page = records_per_page

    def __iter__(self):
        self._iter_index = 0
        return self

    def __next__(self):
        start = self._iter_index
        end = start + self.records_per_page
        if start >= len(self.data):
            raise StopIteration
        records_slice = list(self.data.values())[start:end]
        self._iter_index = end
        return records_slice

    # Добавление записи
    def add_record(self, record):
        self.data[record.name.value] = record

    # Поиск записи
    def find(self, name):
        return self.data.get(name, None)

    # Удаление записи
    def delete(self, name):
        if name in self.data:
            del self.data[name]

    # Поиск по номеру телефона
    def find_by_phone(self, query):
        found_records = []
        for record in self.data.values():
            for phone in record.phones:
                if query.lower() in str(phone).lower():
                    found_records.append(record)
                    break
        return found_records

    # Поиск по имени
    def find_by_name(self, query):
        found_records = []
        for record in self.data.values():
            if query.lower() in record.name.value.lower():
                found_records.append(record)
        return found_records

    # Создание резервной копии
    def start_backup(self, filename):
        with open(filename, 'w') as fn:
            json.dump([{'name': record.name.value,
                        'phones': [phone.value for phone in record.phones],
                        'birthday': record.birthday().strftime("%d.%m.%Y") if record.birthday else None} for record in self.data.values()], fn)

    # Открытие резервной копии
    @classmethod
    def open_backup(cls, filename):
        address_book = cls()
        with open(filename, 'r') as fn:
            data = json.load(fn)
            for record_data in data:
                record = Record(record_data['name'])
                record.phones = [Phone(phone) for phone in record_data.get('phones', [])]
                record.birthday = Birthday(record_data.get('birthday')) if record_data.get('birthday') else None
                address_book.add_record(record)
        return address_book

    def __str__(self):
        return f"Имя: {self.name}, Телефоны: {', '.join(str(phone) for phone in self.phones)}, День рождения: {self.birthday() if self.birthday else 'None'}"


class MyCompleter(Completer):
    def __init__(self, address_book):
        self.address_book = address_book

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if not word_before_cursor:
            for command in ['add_contact', 'add_birthday', 'list_contacts', 'days_to_birthday', 'delete_contact', 'start_backup', 'open_backup', 'exit']:
                yield Completion(command, start_position=0)
        else:
            for command in ['add_contact', 'add_birthday', 'list_contacts', 'days_to_birthday', 'delete_contact',  'start_backup', 'open_backup', 'exit']:
                if word_before_cursor in command:
                    yield Completion(command, start_position=0)


def main():
    address_book = AddressBook()
    file_name = 'back_up.json'

    # Візуалізація проєкту
    while True:
        print('На данный момент существуют такие команды:')
        print('add_contact - Добаление контакта(по желанию сразу и дату рождения).')
        print('add_birthday - Добавления дня рождения к существующему контакту.')
        print('list_contacts - Показывает список конактов.')
        print('days_to_birthday - Показывает сколько осталось до дня рождения существующего контакта, если у него указада дата рожения.')
        print('delete_contact - Удаляет контакт.')
        print('start_backup - Запускает Бэкап контактов, сохраняется файл, после чего его можно открыть и все контакты востанавливаются.')
        print('open_backup - Открывает бэкап')
        print('exit - Выходит из програмы')
        print('\n')
        user_input = prompt('Введите команду: ', completer=MyCompleter(address_book))

        if user_input.startswith('add_contact'):
            name, *phones = input("Введите имя, номер(а) телефона через пробел и дату рождения в формате dd.mm.yyyy (если есть): ").split()
            birthday = None
            if len(phones) > 0 and '/' in phones[-1]: # Проверяем, есть ли последний элемент списка телефонов датой рождения
                birthday = phones.pop()
            record = Record(name, birthday)
            for phone in phones:
                record.add_phone(phone)
            address_book.add_record(record)
        elif user_input.startswith('delete_contact'):
            _, name = input("Введите имя контакта для удаления: ").split()
            address_book.delete(name)
        elif user_input == 'list_contacts':
            print("Список контактов:")
            for name, record in address_book.data.items():
                print(record)
        elif user_input.startswith('start_backup'): 
            address_book.start_backup(file_name)
            print("Резервная копия успешно создана.")
        elif user_input.startswith('open_backup'): 
            address_book = AddressBook.open_backup(file_name)
            print("Резервная копия успешно открыта.")
        elif user_input.startswith('add_birthday'):
            name, birthday = input("Введите имя контакта и дату рождения в формате dd.mm.yyyy: ").split()
            record = address_book.find(name)
            if record:
                record.add_phone(Birthday(birthday))
                print("День рождения успешно добавлен к контакту.")
            else:
                print("Контакт не найден.")
        elif user_input.startswith('days_to_birthday'): 
            name = input("Введите имя контакта: ")
            record = address_book.find(name)
            if record:
                days_left = record.days_to_birthday()
                if days_left is None:
                    print("У контакта нет даты рождения.")
                else:
                    print(f"До дня рождения у контакта {name} осталось {days_left} дней.")
            else:
                print("Контакт не найден.")
        elif user_input == 'exit':
            break
        else:
            print("Неверная команда. Доступные команды: add_contact, delete_contact, list_contacts, backup, days_until_birthday, exit.")
            

if __name__ == "__main__":
    main()