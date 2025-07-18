"""
MIT License.

Copyright (c) 2023 - present Vocard Development

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from collections.abc import Callable
from itertools import cycle

from discord import Member

from .enums import LoopType
from .exceptions import OutofList, QueueFull
from .objects import Track


class LoopTypeCycle:
    def __init__(self) -> None:
        self._cycle = cycle(LoopType)
        self.current = next(self._cycle)

    def next(self) -> LoopType:
        self.current = next(self._cycle)
        return self.current

    def set_mode(self, value: LoopType) -> LoopType:
        while next(self._cycle) != value:
            pass
        self.current = value
        return value

    @property
    def mode(self) -> LoopType:
        return self.current

    def __str__(self) -> str:
        return self.current.name.capitalize()


class Queue:
    def __init__(self, size: int, allow_duplicate: bool, get_msg: Callable[[str], str]) -> None:
        self._queue: list[Track] = []
        self._position: int = 0
        self._size: int = size
        self._repeat: LoopTypeCycle = LoopTypeCycle()
        self._repeat_position: int = 0
        self._allow_duplicate: bool = allow_duplicate

        self.get_msg = get_msg

    def get(self) -> Track | None:
        track = None
        try:
            track = self._queue[self._position - 1 if self._repeat.mode == LoopType.TRACK else self._position]
            if self._repeat.mode != LoopType.TRACK:
                self._position += 1
        except:
            if self._repeat.mode == LoopType.QUEUE:
                try:
                    track = self._queue[self._repeat_position]
                    self._position = self._repeat_position + 1
                except IndexError:
                    self._repeat.set_mode(LoopType.OFF)

        return track

    def put(self, item: Track) -> int:
        if self.count >= self._size:
            raise QueueFull(self.get_msg("voicelinkQueueFull").format(self._size))

        self._queue.append(item)
        return self.count

    def put_at_front(self, item: Track) -> int:
        if self.count >= self._size:
            raise QueueFull(self.get_msg("voicelinkQueueFull").format(self._size))

        self._queue.insert(self._position, item)
        return 1

    def put_at_index(self, index: int, item: Track) -> None:
        if self.count >= self._size:
            raise QueueFull(self.get_msg("voicelinkQueueFull").format(self._size))

        return self._queue.insert(self._position - 1 + index, item)

    def skipto(self, index: int) -> None:
        if not 0 < index <= self.count:
            raise OutofList(self.get_msg("voicelinkOutofList"))
        self._position += index - 1

    def backto(self, index: int) -> None:
        if not self._position - index >= 0:
            raise OutofList(self.get_msg("voicelinkOutofList"))
        self._position -= index

    def history_clear(self, is_playing: bool) -> None:
        self._queue[: self._position - 1 if is_playing else self._position] = []
        self._position = 1 if is_playing else 0

    def clear(self) -> None:
        del self._queue[self._position :]

    def replace(self, queue_type: str, replacement: list) -> None:
        if queue_type == "queue":
            self.clear()
            self._queue += replacement
        elif queue_type == "history":
            self._queue[: self._position] = replacement

    def swap(self, track_index1: int, track_index2: int) -> tuple[Track, Track]:
        try:
            adjusted_position = self._position - 1
            (
                self._queue[adjusted_position + track_index1],
                self._queue[adjusted_position + track_index2],
            ) = (
                self._queue[adjusted_position + track_index2],
                self._queue[adjusted_position + track_index1],
            )
            return self._queue[adjusted_position + track_index1], self._queue[adjusted_position + track_index2]
        except IndexError:
            raise OutofList(self.get_msg("voicelinkOutofList"))

    def move(self, target: int, to: int) -> Track | None:
        if not 0 < target <= self.count or not to > 0:
            raise OutofList(self.get_msg("voicelinkOutofList"))

        try:
            item = self._queue[self._position + target - 1]
            self._queue.remove(item)
            self.put_at_index(to, item)
            return item
        except:
            raise OutofList(self.get_msg("voicelinkOutofList"))

    def remove(self, index: int, index2: int | None = None, member: Member = None) -> dict[int, Track]:
        pos = self._position - 1

        if index2 is None:
            index2 = index

        elif index2 < index:
            index, index2 = index2, index

        try:
            removed_tracks: dict[str, Track] = {}
            for i, track in enumerate(self._queue[pos + index : pos + index2 + 1]):
                if member and track.requester != member:
                    continue

                self._queue.remove(track)
                removed_tracks[pos + index + i] = track

            return removed_tracks
        except:
            raise OutofList(self.get_msg("voicelinkOutofList"))

    def history(self, incTrack: bool = False) -> list[Track]:
        if incTrack:
            return self._queue[: self._position]
        return self._queue[: self._position - 1]

    def tracks(self, incTrack: bool = False) -> list[Track]:
        if incTrack:
            return self._queue[self._position - 1 :]
        return self._queue[self._position :]

    @property
    def count(self) -> int:
        return len(self._queue[self._position :])

    @property
    def repeat(self) -> str:
        return self._repeat.mode.name.capitalize()

    @property
    def is_empty(self) -> bool:
        try:
            self._queue[self._position]
        except:
            return True
        return False


class FairQueue(Queue):
    def __init__(self, size: int, allow_duplicate: bool, get_msg) -> None:
        super().__init__(size, allow_duplicate, get_msg)
        self._set = set()

    def put(self, item: Track) -> int:
        if len(self._queue) >= self._size:
            raise QueueFull(self.get_msg("voicelinkQueueFull").format(self._size))

        tracks = self.tracks(incTrack=True)
        lastIndex = len(tracks)
        for track in reversed(tracks):
            if track.requester == item.requester:
                break
            lastIndex -= 1
        self._set.clear()
        for track in tracks[lastIndex:]:
            if track.requester in self._set:
                break
            lastIndex += 1
            self._set.add(track.requester)

        self.put_at_index(lastIndex, item)
        return lastIndex
