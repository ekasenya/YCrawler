from html.parser import HTMLParser


class HTMLNewsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.link_list = []
        self.current_id = 0

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'tr':
            is_athing = False
            id = 0
            for name, value in attrs:
                if name.lower() == 'class' and value.lower() == 'athing':
                    is_athing = True
                elif name.lower() == 'id':
                    id = value

            if is_athing:
                self.current_id = id

        if tag.lower() == 'a':
            href = ''
            is_storylink = False
            for name, value in attrs:
                if name.lower() == 'class' and value.lower() == 'storylink':
                    is_storylink = True
                elif name.lower() == 'href':
                    href = value

            if is_storylink and self.current_id:
                self.link_list.append({'ID': self.current_id, 'URL': href})
                self.current_id = 0


class HTMLCommentsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.comment_list = []
        self.is_comment = False
        self.inner_span_counter = 0

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'span':
            if self.is_comment:
                self.inner_span_counter += 1
            else:
                self.is_comment = False
                for name, value in attrs:
                    if name.lower() == 'class' and value.lower() == 'commtext c00':
                        self.is_comment = True
        elif tag.lower() == 'a' and self.is_comment:
            for name, value in attrs:
                if name.lower() == 'href':
                    self.comment_list.append(value)

    def handle_endtag(self, tag):
        if tag.lower() == 'span' and self.is_comment:
            self.inner_span_counter -= 1
            if self.inner_span_counter < 0:
                self.is_comment = False
                self.inner_span_counter = 0



