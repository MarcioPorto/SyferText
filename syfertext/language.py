# Author: Alan Aboudib

from .tokenizer import Tokenizer
from .pointers.tokenizer_pointer import TokenizerPointer
from .vocab import Vocab

from syft.generic.object import AbstractObject
from syft.workers.base import BaseWorker
from syft.generic.string import String
from syft.generic.pointers.string_pointer import StringPointer
from typing import List, Union


class BaseDefaults(object):
    """
       A class that defines all the defaults of the Language class
    """

    @classmethod
    def create_vocab(cls, model_name):
        """
           Creates the Vocab object that holds the vocabulary along with vocabulary meta data

           Todo:
               I started by a very simple Vocab class that
               contains only a variable called 'vectors' of type DICT to hold word vectors
               vocab.vectors['word'] = float. To be reviewed for more complex functionality.
        """

        # Instantiate the Vocab object
        vocab = Vocab(model_name)

        return vocab

    @classmethod
    def create_tokenizer(
        cls,
        vocab,
        id: int = None,
        owner: BaseWorker = None,
        client_id: BaseWorker = None,
        tags: List[str] = None,
        description: str = None,
    ):
        """Creates a Tokenizer object that will be used to create the Doc object, which is the 
        main container for annotated tokens.

           Todo:
               this is a minimal Tokenizer object that is not nearly as sophisticated
               as that of spacy. It just creates tokens as space separated strings. 
               Something like "string1 string2".split(' '). Of course, this should be changed later.
        """

        # Instantiate the Tokenizer object and return it
        tokenizer = Tokenizer(
            vocab,
            owner=owner,
            client_id=client_id,  # This is the id of the owner of the Language object using this tokenizer
            tags=tags,
            description=description,
        )

        return tokenizer


class Language(AbstractObject):
    """Orchestrates the interactions between different components of the pipeline
    to accomplish core text-processing task. 

    It create the Doc object which is the container into which all text-processing
    pipeline components feed their results.
    """

    def __init__(
        self,
        model_name,
        id: int = None,
        owner: BaseWorker = None,
        tags: List[str] = None,
        description: str = None,
    ):

        # Define the default settings
        self.Defaults = BaseDefaults

        # Create the vocabulary
        self.vocab = self.Defaults.create_vocab(model_name)

        # Create a dictionary that associates to the name of each text-processing compomenet
        # of the pipeline, an object that is charged to accomplish the job.
        self.factories = {"tokenizer": self.Defaults.create_tokenizer}

        self.tokenizer = None

        super(Language, self).__init__(
            id=id, owner=owner, tags=tags, description=description
        )

    def make_doc(self, text: Union[str, String, StringPointer]):
        """Creates a Tokenizer object and uses it to tokenize 'text'. The tokens
        are stored in a Doc object which is then returned.
        """

        # TODO: huge bugs in this function. deal with the case when the function a local string `text`
        #       after it has been already called with a remote string
        if self.tokenizer is None:

            # Create the Tokenizer object
            self.tokenizer = self.factories["tokenizer"](
                self.vocab,
                owner=self.owner,
                client_id=self.owner.id,  # This is the id of the owner of the Language object using this tokenizer
            )

        # If `text` is of type `StringPointer` and the pointer's `location` attribute
        # is a worker different from the current Language object' owner, then run
        # tokenization remotely
        if isinstance(text, StringPointer) and text.location != self.owner:

            if (
                isinstance(self.tokenizer, TokenizerPointer)
                and self.tokenizer.location == text.location
            ):
                pass

            elif (
                isinstance(self.tokenizer, TokenizerPointer)
                and self.tokenizer.location != text.location
            ):

                # Create a new Tokenizer object
                self.tokenizer = self.factories["tokenizer"](
                    self.vocab,
                    owner=self.owner,
                    client_id=self.owner.id,  # This is the id of the owner of the Language object using this tokenizer
                )

                # Send the tokenizer to the worker where `text` lives
                self.tokenizer = self.tokenizer.send(text.location)

            else:
                # Send the tokenizer to the worker where `text` lives
                self.tokenizer = self.tokenizer.send(text.location)

        # Tokenize the text
        doc = self.tokenizer(text)

        # Return the Doc object containing the tokens
        return doc

    def __call__(self, text):
        """Here is where the real work is done. The pipeline components
        are called here, and the Doc object containing their results is created
        here too.
        """

        # create the Doc object with the tokenized text in it
        doc = self.make_doc(text)

        # TODO: Other pipline components should be called here and attach
        # their results to tokens in 'doc'

        # return the Doc object
        return doc
