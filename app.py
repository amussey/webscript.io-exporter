import click
import json
import os
import requests


class Webscript(object):

    def __init__(self, username, api_key, export_dir='./export', path='https://www.webscript.io/api/0.1', debug=True):
        self.auth = requests.auth.HTTPBasicAuth(username, api_key)
        self.export_dir = export_dir
        self.path = path
        self.debug = debug

        if not os.path.isdir(self.export_dir):
            os.makedirs(self.export_dir)

    def request(self, endpoint, is_json=True):
        url = '{}{}'.format(self.path, endpoint)
        response = requests.get(url, auth=self.auth)

        if is_json:
            return response.json()
        return response.text

    def _save_file(self, filename, response, is_json=True):
        export_filename = '{}/{}'.format(self.export_dir, filename)

        file = open(export_filename, 'w')
        if is_json:
            file.write(json.dumps(response, indent=4))
        else:
            file.write(response)
        file.close()

        if self.debug:
            print(export_filename)

    def _save_json(self, filename, response):
        self._save_file(filename, response, True)

    def _save_lua(self, filename, response):
        self._save_file(filename, response, False)

    def export(self):
        subdomains = self.export_subdomains()

        for subdomain, scripts in subdomains.items():
            endpoints = scripts.get('scripts', [])
            self.export_scripts(subdomain, endpoints)

    def export_subdomains(self):
        subdomains = self.request('/subdomains')
        self._save_json('subdomains.json', subdomains)

        return subdomains

    def export_scripts(self, subdomain, endpoints=None):
        if endpoints is None:
            subdomains = self.request('/subdomains')
            endpoints = subdomains.get(subdomain, {}).get('scripts', [])

        output_dir = '{}/{}'.format(self.export_dir, subdomain)

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        for endpoint in endpoints:
            url = '/script/{}{}'.format(subdomain, endpoint)
            script = self.request(url, is_json=False)

            header = '-- Subdomain: {}\n-- Endpoint:  {}\n\n'.format(subdomain, endpoint)
            output = '{}{}'.format(header, script)

            filename_lua = '{}.lua'.format(endpoint[1:].replace('/', '-'))
            if filename_lua == '.lua':
                filename_lua = '__base__.lua'

            filepath = '{}/{}'.format(
                subdomain,
                filename_lua,
            )

            self._save_lua(filepath, output)


@click.command()
@click.option('--username', prompt='Your username/email', help='Your login username/email')
@click.option('--api-key', prompt='Your API key (from https://www.webscript.io/settings)', help='Your API key (from https://www.webscript.io/settings)')
def main(username, api_key):
    webscript = Webscript(username, api_key)
    webscript.export()


if __name__ == '__main__':
    main()
